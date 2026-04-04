import os
import sys

import click
from dotenv import load_dotenv

from src.runner import run_outreach

load_dotenv()


@click.command()
@click.option("--criteria", required=True, help='Search keyword, e.g. "co-founder"')
@click.option("--max-results", default=50, show_default=True, help="Max profiles to scrape")
@click.option(
    "--output-dir",
    default="output",
    show_default=True,
    help="Directory to write verified_leads.csv and rejected_leads.csv",
)
@click.option(
    "--cookies-file",
    default=os.getenv("LINKEDIN_COOKIES_FILE", "linkedin_cookies.json"),
    show_default=True,
    help="Path to LinkedIn session cookie file",
)
def main(criteria, max_results, output_dir, cookies_file):
    """
    Scrape LinkedIn for people matching CRITERIA, find and verify their emails
    without any paid API tokens, and save results to local CSV files.
    """
    result = run_outreach(
        criteria=criteria,
        max_results=max_results,
        output_dir=output_dir,
        cookies_file=cookies_file,
        log=click.echo,
    )

    if not result["profiles_found"]:
        click.echo("No profiles found. Check your criteria or LinkedIn session.")
        sys.exit(0)

    click.echo("")
    click.echo("Done.")
    click.echo(f"  Verified  -> {output_dir}/verified_leads.csv  : {result['verified']}")
    click.echo(f"  Rejected  -> {output_dir}/rejected_leads.csv  : {result['rejected']}")
    click.echo(f"  Skipped   (errors)                           : {result['skipped']}")


if __name__ == "__main__":
    main()
