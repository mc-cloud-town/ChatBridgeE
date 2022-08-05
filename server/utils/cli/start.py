import click


@click.command()
@click.argument("type", default="base")
def main(type):
    print(type)


def start_base_server():
    ...
