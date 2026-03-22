import time
from django.core.management.base import BaseCommand
from events.models import Event
from swipes.ml import SwipeML
from tqdm import tqdm


class Command(BaseCommand):
    help = 'Массовая генерация эмбеддингов для событий'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=32,
            help='Размер пачки для обработки за один раз (по умолчанию: 32)'
        )

    def handle(self, *args, **options):
        qs = list(Event.objects.filter(is_published=True))  # regenerate for all
        total = len(qs)

        batch_size = options['batch_size']

        SwipeML.init()

        num_batches = (total + batch_size - 1) // batch_size
        for i in tqdm(range(num_batches), desc="Generating embeddings"):
            batch_events = qs[i*batch_size:(i+1)*batch_size]
            texts = [event.full_text for event in batch_events]
            embeddings = SwipeML.get_embeddings(texts)

            for event, embedding in zip(batch_events, embeddings):
                event.embedding = embedding
                event.save(update_fields=['embedding'])

