import environ
from django.core.management.base import BaseCommand
from pydrive.auth import GoogleAuth


def google_authenticate(
    credentials: str, authorized_user: str, force_new: bool = False
):
    """
    Authenticate with Google.

    Parameters
    ----------
    credentials : str
        The path to the credentials file.
    authorized_user : str
        The authorized user email.
    """
    # Authenticate and create the PyDrive client
    gauth = GoogleAuth()
    gauth.settings["client_config_file"] = credentials
    # Check whether the credentials are expired
    if gauth.credentials is None or gauth.access_token_expired or force_new:
        print("Google credentials are expired or not found.")  # noqa: T201
        print("Authenticating with Google...")  # noqa: T201
        # Authenticate if credentials are not there
        # gauth.LocalWebserverAuth()
        gauth.CommandLineAuth()
        gauth.SaveCredentialsFile(authorized_user)
    else:
        # Initialize the saved credentials
        gauth.LoadCredentialsFile(authorized_user)
        gauth.Authorize()
    # Save the current credentials to a file for future use
    gauth.SaveCredentialsFile(authorized_user)


class Command(BaseCommand):
    help = "Update the database with information from an Excel file."
    env = environ.Env()
    credentials = env("GSPREAD_CREDENTIALS", default=None)
    authorized_user = env("GSPREAD_AUTHORIZED_USER", default=None)

    def add_arguments(self, parser):
        parser.add_argument(
            "--credentials",
            type=str,
            nargs="?",
            help="Path to the credentials file",
            default=self.credentials,
        )
        parser.add_argument(
            "--authorized_user",
            type=str,
            nargs="?",
            help="Authorized user email",
            default=self.authorized_user,
        )

    def handle(self, *args, **kwargs):
        credentials = kwargs["credentials"]
        authorized_user = kwargs["authorized_user"]
        google_authenticate(credentials, authorized_user)
        self.stdout.write(self.style.SUCCESS("Google authenticated successfully."))


if __name__ == "__main__":
    env = environ.Env()
    credentials = env("GSPREAD_CREDENTIALS", default=None)
    authorized_user = env("GSPREAD_AUTHORIZED_USER", default=None)
    google_authenticate(credentials, authorized_user)
