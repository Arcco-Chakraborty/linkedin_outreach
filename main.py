import os
import sys

import click
from dotenv import load_dotenv

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
    from src.session import get_authenticated_context
    from src.scraper import search_people
    from src.sheets_writer import CSVWriter
    from src.pipeline import run_pipeline

    click.echo(f"[1/4] Authenticating with LinkedIn (cookies: {cookies_file})...")
    context = get_authenticated_context(cookies_file)

    click.echo(f"[2/4] Searching LinkedIn for '{criteria}' (max {max_results})...")
    profiles = search_people(context, criteria=criteria, max_results=max_results)
    if not profiles:
        click.echo("No profiles found. Check your criteria or LinkedIn session.")
        sys.exit(0)
    click.echo(f"      Found {len(profiles)} profiles.")

    click.echo(f"[3/4] Preparing output directory: '{output_dir}'...")
    writer = CSVWriter(output_dir=output_dir)

    click.echo("[4/4] Finding and verifying emails (this may take a few minutes)...")
    verified, rejected, skipped = run_pipeline(
        profiles=profiles,
        context=context,
        writer=writer,
    )

    click.echo("")
    click.echo("Done.")
    click.echo(f"  Verified  → {output_dir}/verified_leads.csv  : {verified}")
    click.echo(f"  Rejected  → {output_dir}/rejected_leads.csv  : {rejected}")
    click.echo(f"  Skipped   (errors)                           : {skipped}")


if __name__ == "__main__":
    main()
