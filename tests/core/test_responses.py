from crm.core.responses import redirect_with_error


def test_redirect_with_error_appends_a_quoted_error_query_param() -> None:
    response = redirect_with_error("/contacts/1", "name cannot be empty")

    assert response.headers["location"] == "/contacts/1?error=name%20cannot%20be%20empty"
    assert response.status_code == 303


def test_redirect_with_error_appends_with_ampersand_when_url_already_has_a_query() -> None:
    response = redirect_with_error("/contacts/1?tab=notes", "boom")

    assert response.headers["location"] == "/contacts/1?tab=notes&error=boom"


def test_redirect_with_error_leaves_the_url_untouched_when_there_is_no_error() -> None:
    response = redirect_with_error("/contacts/1", None)

    assert response.headers["location"] == "/contacts/1"
