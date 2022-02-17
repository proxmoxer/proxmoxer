try:
    from shlex import join

    def shelljoin(args):
        return join(args)

except ImportError:
    try:
        from shlex import quote
    except ImportError:
        from shellescape import quote

    def shelljoin(args):
        return " ".join([quote(arg) for arg in args])
