def format_author(author):
    if author is None:
        return "Anonymous"

    if "/users/" in author:
        return (
            author
            .split("/users/", 1)[1]
            .split("/", 1)[0]
        )

    return author