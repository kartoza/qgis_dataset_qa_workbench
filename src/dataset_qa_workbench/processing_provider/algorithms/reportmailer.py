import json
import smtplib
import typing
from email.message import EmailMessage

from qgis.core import (
    QgsProcessingOutputBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterExpression,
    QgsProcessingParameterString,
)

from ...datasetqaworkbench import utils
from ...datasetqaworkbench.constants import (
    QGIS_VARIABLE_PREFIX,
    REPORT_HANDLER_INPUT_NAME,
)


from .base import (
    BaseAlgorithm,
    parse_as_expression,
)


class ReportMailerAlgorithm(BaseAlgorithm):
    INPUT_REPORT_FORMAT = "INPUT_REPORT_FORMAT"
    INPUT_SENDER_ADDRESS = "INPUT_SENDER_ADDRESS"
    INPUT_SENDER_PASSWORD = "INPUT_SENDER_PASSWORD"
    INPUT_RECIPIENTS = "INPUT_RECIPIENTS"
    INPUT_SMTP_HOST = "INPUT_SMTP_HOST"
    INPUT_SMTP_PORT = "INPUT_SMTP_PORT"
    INPUT_SMTP_SECURE_CONNECTION = "INPUT_SMTP_SECURE_CONNECTION"
    OUTPUT_MAIL_SENT = "MAIL_SENT"

    REPORT_FORMATS = [
        ("plain text", utils.serialize_report_to_plain_text),
        ("json", json.dumps),
    ]

    def name(self):
        return "reportmailer"

    def displayName(self):
        return self.tr("Report mailer")

    def createInstance(self):
        return ReportMailerAlgorithm()

    def shortHelpString(self):
        return self.tr(
            "This algorithm will email the generated validation report to a "
            "set of designated recipients.\n\n"
            "In order to be easily automatable, the algorithm can be "
            "configured by setting the following QGIS global variables "
            "(go to Settings -> Options... -> Variables): "
            "\n\n"
            "- dataset_qa_workbench_sender_address: email address of the "
            "sender\n"
            "- dataset_qa_workbench_sender_password: password of the sender\n"
            "- dataset_qa_workbench_recipients: email addresses that will "
            "receive the validation report. Supply a space-separated list of "
            "addresses\n"
            "- dataset_qa_workbench_smtp_host: SMTP host. If not specified, "
            "this defaults to `smtp.gmail.com`\n"
            "- dataset_qa_workbench_smtp_port: SMTP port. If not specified, "
            "this defaults to `587`\n"
            "- dataset_qa_workbench_smtp_secure_connection: Connection "
            "security options. Acceptable values are: `starttls`, `ssl`, or "
            "just omit this in order to use no security. If not specified, "
            "this defaults to `starttls`"
        )

    def initAlgorithm(self, configuration, p_str=None, Any=None, *args, **kwargs):
        self.addParameter(
            QgsProcessingParameterString(
                REPORT_HANDLER_INPUT_NAME,
                self.tr("Input validation report"),
                defaultValue="{}",
                multiLine=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.INPUT_REPORT_FORMAT,
                self.tr("Report format"),
                options=[i[0] for i in self.REPORT_FORMATS],
                defaultValue=self.REPORT_FORMATS[0][0],
            )
        )
        self.addParameter(
            QgsProcessingParameterExpression(
                self.INPUT_SENDER_ADDRESS,
                self.tr("Sender email"),
                defaultValue=f"@{QGIS_VARIABLE_PREFIX}_sender_address",
            )
        )
        self.addParameter(
            QgsProcessingParameterExpression(
                self.INPUT_SENDER_PASSWORD,
                self.tr("Sender password"),
                defaultValue=f"@{QGIS_VARIABLE_PREFIX}_sender_password",
            )
        )
        self.addParameter(
            QgsProcessingParameterExpression(
                self.INPUT_RECIPIENTS,
                self.tr("Recipients"),
                defaultValue=(f"string_to_array(@{QGIS_VARIABLE_PREFIX}_recipients)"),
            )
        )
        self.addParameter(
            QgsProcessingParameterExpression(
                self.INPUT_SMTP_HOST,
                self.tr("SMTP host"),
                defaultValue=(
                    f"coalesce(@{QGIS_VARIABLE_PREFIX}_smtp_host, " f"'smtp.gmail.com')"
                ),
            )
        )
        self.addParameter(
            QgsProcessingParameterExpression(
                self.INPUT_SMTP_PORT,
                self.tr("SMTP port"),
                defaultValue=(f"coalesce(@{QGIS_VARIABLE_PREFIX}_smtp_port, 587)"),
            )
        )
        self.addParameter(
            QgsProcessingParameterExpression(
                self.INPUT_SMTP_SECURE_CONNECTION,
                self.tr("Connection security method to use when sending email"),
                defaultValue=(
                    f"coalesce(@{QGIS_VARIABLE_PREFIX}_smtp_secure_connection,"
                    f"'starttls')"
                ),
            )
        )
        self.addOutput(
            QgsProcessingOutputBoolean(
                self.OUTPUT_MAIL_SENT, "Was the email sent or not"
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        raw_report = self.parameterAsString(
            parameters, REPORT_HANDLER_INPUT_NAME, context
        )
        report = json.loads(raw_report)
        report_format_index = self.parameterAsEnum(
            parameters, self.INPUT_REPORT_FORMAT, context
        )
        serialized_report = self._serialize_report(report, report_format_index)
        feedback.pushInfo(f"serialized_report: {serialized_report}")

        sender_address = parse_as_expression(
            self.parameterAsExpression(parameters, self.INPUT_SENDER_ADDRESS, context)
        )
        feedback.pushInfo(f"sender_address: {sender_address}")
        sender_password = parse_as_expression(
            self.parameterAsExpression(parameters, self.INPUT_SENDER_PASSWORD, context)
        )
        feedback.pushInfo(f"sender_password: {sender_password}")
        recipients = parse_as_expression(
            self.parameterAsExpression(parameters, self.INPUT_RECIPIENTS, context),
            default=[],
        )
        feedback.pushInfo(f"recipients: {recipients}")
        smtp_host = parse_as_expression(
            self.parameterAsExpression(parameters, self.INPUT_SMTP_HOST, context)
        )
        smtp_port = parse_as_expression(
            self.parameterAsExpression(parameters, self.INPUT_SMTP_PORT, context)
        )
        smtp_secure_connection = parse_as_expression(
            self.parameterAsExpression(
                parameters, self.INPUT_SMTP_SECURE_CONNECTION, context
            )
        )
        subject = "QGIS Dataset QA Workbench plugin - Validation report"
        extra_kwargs = {}
        if smtp_host is not None:
            extra_kwargs["smtp_host"] = smtp_host
        if smtp_port is not None:
            extra_kwargs["smtp_port"] = int(smtp_port)
        if smtp_secure_connection is not None:
            extra_kwargs["smtp_secure_connection"] = smtp_secure_connection
        feedback.pushInfo(f"subject: {subject}")
        feedback.pushInfo(f"extra_kwargs: {extra_kwargs}")
        sent, errors = send_mail(
            sender_address,
            sender_password,
            subject,
            serialized_report,
            recipients=recipients,
            **extra_kwargs,
        )
        for error, is_fatal in errors:
            feedback.reportError(error, fatalError=is_fatal)
        return {self.OUTPUT_MAIL_SENT: sent}

    def _serialize_report(self, report: typing.Dict, selected_index: int):
        handler = self.REPORT_FORMATS[selected_index][1]
        return handler(report)


def send_mail(
    sender: str,
    sender_password: str,
    subject: str,
    message: str,
    recipients: typing.List[str],
    smtp_host: typing.Optional[str] = "smtp.gmail.com",
    smtp_port: typing.Optional[int] = 587,
    smtp_secure_connection: typing.Optional[str] = "starttls",
) -> typing.Tuple[bool, typing.List[typing.Tuple[str, bool]]]:
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(message)
    errors = []
    try:
        if smtp_secure_connection == "starttls":
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.ehlo()
            server.starttls()
        elif smtp_secure_connection == "ssl":
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
            server.ehlo()
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.ehlo()
    except smtplib.SMTPException as exc:
        result = False
        errors.append((str(exc), True))
    else:
        server.login(sender, sender_password)
        try:
            sent_to: typing.Dict = server.send_message(msg)
        except smtplib.SMTPException as exc:
            result = False
            errors.append((str(exc), True))
        else:
            for recipient, error_info in sent_to.items():
                errors.append(
                    (f"Could not send report to {recipient!r}: {error_info}", False)
                )
            result = len(sent_to) == 0
        server.quit()
    return result, errors
