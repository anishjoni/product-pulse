"""
ScoutRunner — orchestrates a full data-ingestion + classification run for a single product.

Workflow:
  1. Load product from ProductRepository.
  2. Create a scout_run record with status='running'.
  3. Run RedditScraper and YouTubeScraper, inserting results via RawFeedbackRepository.
  4. Mark the run as 'completed' (or 'failed' on any exception).
  5. Classify all newly ingested items via LLMClassifier and store results.
  6. Update scout_run.items_classified with the count of classified items.
"""

import logging

from src.analysis.trend_analyser import TrendAnalyser
from src.db.repositories.classified_feedback_repository import ClassifiedFeedbackRepository
from src.db.repositories.product_repository import ProductRepository
from src.db.repositories.raw_feedback_repository import RawFeedbackRepository
from src.db.repositories.scout_run_repository import ScoutRunRepository
from src.ingestion.reddit_scraper import RedditScraper
from src.ingestion.youtube_scraper import YouTubeScraper
from src.llm.classifier import LLMClassifier

logger = logging.getLogger(__name__)


class ScoutRunner:
    """Runs a full ingestion scout for one product."""

    def __init__(self) -> None:
        self._product_repo = ProductRepository()
        self._run_repo = ScoutRunRepository()
        self._feedback_repo = RawFeedbackRepository()
        self._classified_repo = ClassifiedFeedbackRepository()
        self._reddit = RedditScraper()
        self._youtube = YouTubeScraper()
        self._classifier = LLMClassifier()
        self._trend_analyser = TrendAnalyser()

    def run(self, product_id: int, triggered_by: str = "manual") -> dict:
        """
        Execute a full scout run for the given product.

        Returns the scout_run dict (with final status, items_fetched, etc.).
        Raises the original exception if the run fails so the caller can return
        an appropriate HTTP error.
        """
        # 1. Load product — raises if not found (intentional, caller should 404)
        product = self._product_repo.get_by_id(product_id)
        if product is None:
            raise ValueError(f"Product {product_id} not found.")

        # 2. Create scout_run record (status='running')
        scout_run = self._run_repo.create(
            product_id=product_id, triggered_by=triggered_by
        )
        run_id: int = scout_run["id"]
        logger.info(
            "Scout run #%d started for product '%s' (triggered_by=%s).",
            run_id,
            product.get("name"),
            triggered_by,
        )

        try:
            # 3a. Reddit
            reddit_items = self._reddit.fetch(product)
            reddit_inserted = self._feedback_repo.insert_many(
                reddit_items, product_id, run_id
            )
            logger.info(
                "Run #%d — Reddit: fetched=%d, inserted=%d.",
                run_id,
                len(reddit_items),
                reddit_inserted,
            )

            # 3b. YouTube — filter to items that mention at least one product keyword
            # (YouTube search results include unrelated videos whose comments have
            #  no mention of the product at all)
            youtube_items = self._youtube.fetch(product)
            keywords = [kw.lower() for kw in product.get("keywords", [])]
            if keywords:
                before = len(youtube_items)
                youtube_items = [
                    item for item in youtube_items
                    if any(kw in item.content.lower() for kw in keywords)
                ]
                logger.info(
                    "Run #%d — YouTube relevance filter: %d → %d items.",
                    run_id, before, len(youtube_items),
                )
            youtube_inserted = self._feedback_repo.insert_many(
                youtube_items, product_id, run_id
            )
            logger.info(
                "Run #%d — YouTube: fetched=%d, inserted=%d.",
                run_id,
                len(youtube_items),
                youtube_inserted,
            )

            # 3c. Total inserted
            total_inserted = reddit_inserted + youtube_inserted

            # 4. Mark ingestion as completed (classification updates items_classified next)
            self._run_repo.complete(run_id, items_fetched=total_inserted)
            logger.info(
                "Scout run #%d ingestion completed. items_fetched=%d.", run_id, total_inserted
            )

            # 5. Classify all unclassified items from this run
            unclassified = self._feedback_repo.get_unclassified(product_id, run_id)
            classified_count = 0
            for raw_item in unclassified:
                result = self._classifier.classify(raw_item, product)
                if result["classification_status"] == "success":
                    self._classified_repo.insert(
                        raw_feedback_id=raw_item["id"],
                        category=result["category"],
                        sentiment=result["sentiment"],
                        summary=result["summary"],
                        topics=result["topics"],
                        confidence=result["confidence"],
                        llm_provider=result["llm_provider"],
                    )
                else:
                    self._classified_repo.insert_failed(
                        raw_item["id"], result["llm_provider"]
                    )
                classified_count += 1

            # 6. Update items_classified on the scout run record
            self._run_repo.update_classified(run_id, classified_count)
            logger.info(
                "Scout run #%d classification completed. items_classified=%d.",
                run_id,
                classified_count,
            )

            # 7. Compute trends — runs after every scout run; idempotent
            try:
                trends = self._trend_analyser.compute_trends(product_id)
                logger.info(
                    "Scout run #%d — computed %d trends for product %d.",
                    run_id,
                    len(trends),
                    product_id,
                )
            except Exception as trend_exc:
                # Trend computation failure must not fail the scout run itself
                logger.error(
                    "Scout run #%d — trend computation failed (non-fatal): %s",
                    run_id,
                    trend_exc,
                    exc_info=True,
                )

        except Exception as exc:
            # Mark as failed, then re-raise so the API can return 500
            self._run_repo.fail(run_id, str(exc))
            logger.error("Scout run #%d failed: %s", run_id, exc, exc_info=True)
            raise

        # Return the final state of the run record
        return self._run_repo.get_by_id(run_id)
