class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://shecktar:Shecktar13$@localhost/test_stockguard"
    SECRET_KEY = "test_secret_key"
    MAIL_SUPPRESS_SEND = True  # Disable email sending during tests
    MAIL_DEFAULT_SENDER = "test@example.com"
