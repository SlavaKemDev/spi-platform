from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from organizations.models import Organization
from events.models import Event


SEED_DATA = [
    {
        'org_name': 'AI Community Russia',
        'title': 'Хакатон по AI и машинному обучению',
        'description': (
            '48 часов непрерывной разработки прорывных решений в области искусственного интеллекта '
            'и машинного обучения. Призовой фонд — 500 000 ₽. Приглашаем команды до 5 человек и '
            'одиночных участников. Организаторы обеспечат питание, рабочие места и менторство от '
            'экспертов Яндекса, Сбера и ВКонтакте. Регистрация обязательна, количество мест ограничено.'
        ),
        'location': 'Технопарк «Сколково», Москва',
        'format': Event.Format.OFFLINE,
        'categories': ['it', 'hackathon'],
        'access_type': 'open',
        'reg_opens': 0,
        'reg_closes': 10,
        'event_starts': 15,
        'event_ends': 17,
    },
    {
        'org_name': 'Физический факультет МГУ',
        'title': 'Открытая лекция: Квантовые вычисления',
        'description': (
            'Профессор Алексей Иванов расскажет о последних достижениях в области квантовых вычислений '
            'и их практическом применении в криптографии и комбинаторной оптимизации. '
            'Лекция предназначена для студентов старших курсов, аспирантов и всех, кто интересуется '
            'квантовыми технологиями. Вход свободный, регистрация приветствуется.'
        ),
        'location': 'МГУ, Главное здание, ауд. 12',
        'format': Event.Format.OFFLINE,
        'categories': ['lecture', 'it'],
        'access_type': 'open',
        'reg_opens': 0,
        'reg_closes': 18,
        'event_starts': 22,
        'event_ends': 22,
    },
    {
        'org_name': 'HR Community Moscow',
        'title': 'Карьерная ярмарка — IT & Tech 2026',
        'description': (
            'Встречайтесь с HR-специалистами и руководителями топовых IT-компаний. '
            'Более 80 корпоративных стендов, мастер-классы по составлению резюме и прохождению '
            'интервью, mock-интервью с экспертами из Яндекса, VK, Сбера, Тинькофф и других компаний. '
            'Приходите с распечатанным резюме и открытым сердцем — здесь начинаются карьеры.'
        ),
        'location': 'Экспоцентр, павильон 7, Москва',
        'format': Event.Format.OFFLINE,
        'categories': ['networking', 'it'],
        'access_type': 'open',
        'reg_opens': 0,
        'reg_closes': 25,
        'event_starts': 29,
        'event_ends': 29,
    },
    {
        'org_name': 'Web3 Moscow Community',
        'title': 'Митап: Web3 и децентрализованные приложения',
        'description': (
            'Обсудим реальные кейсы внедрения dApp в финансах и логистике. '
            'Разберём современные инструменты разработки смарт-контрактов на Solidity и Rust, '
            'новые стандарты безопасности аудитов и актуальные тренды рынка Web3. '
            'Ссылку на подключение вышлем на почту после регистрации.'
        ),
        'location': 'Онлайн (Zoom)',
        'format': Event.Format.ONLINE,
        'categories': ['it', 'networking', 'startup'],
        'access_type': 'open',
        'reg_opens': 0,
        'reg_closes': 12,
        'event_starts': 14,
        'event_ends': 14,
    },
    {
        'org_name': 'UX School Moscow',
        'title': 'Воркшоп по UX/UI Design Thinking',
        'description': (
            'Практический однодневный интенсив по методологии дизайн-мышления. '
            'Вы научитесь создавать пользовательские сценарии, разрабатывать прототипы в Figma, '
            'а также проводить юзабилити-тесты с реальными пользователями. '
            'Воркшоп ведут практикующие UX-дизайнеры из Авито и Ozon. Количество мест — 20.'
        ),
        'location': 'Дизайн-центр Artplay, Москва',
        'format': Event.Format.OFFLINE,
        'categories': ['masterclass', 'self_dev'],
        'access_type': 'open',
        'reg_opens': 0,
        'reg_closes': 35,
        'event_starts': 40,
        'event_ends': 40,
    },
    {
        'org_name': 'Data Science Community',
        'title': 'Конференция: Data Science в бизнесе',
        'description': (
            'Более 20 докладов о реальном применении data science в ритейле, банкинге и здравоохранении. '
            'Узнайте, как ведущие компании строят рекомендательные системы, детектируют мошенничество '
            'и внедряют предиктивную аналитику. Нетворкинг-сессии, стенды партнёров и вечерняя afterparty.'
        ),
        'location': 'Digital October, Москва',
        'format': Event.Format.OFFLINE,
        'categories': ['it', 'lecture', 'networking'],
        'access_type': 'open',
        'reg_opens': 0,
        'reg_closes': 50,
        'event_starts': 55,
        'event_ends': 55,
    },
    {
        'org_name': 'CyberSec Hub Russia',
        'title': 'CTF: Соревнование по кибербезопасности',
        'description': (
            'Capture The Flag — 24-часовое онлайн-соревнование для студентов и молодых специалистов. '
            'Категории задач: web exploitation, reverse engineering, cryptography, forensics и pwn. '
            'Задания трёх уровней сложности подойдут как новичкам, так и опытным участникам. '
            'Лучшие команды получат приглашения в финал и ценные призы от спонсоров.'
        ),
        'location': 'Онлайн',
        'format': Event.Format.ONLINE,
        'categories': ['it', 'hackathon'],
        'access_type': 'open',
        'reg_opens': 0,
        'reg_closes': 60,
        'event_starts': 62,
        'event_ends': 63,
    },
    {
        'org_name': 'Startup Russia Foundation',
        'title': 'StartUp Weekend: Питч-сессия стартапов',
        'description': (
            'Три дня от идеи до готового MVP. В пятницу генерируем идеи и собираем команды, '
            'в субботу работаем над прототипом с менторами из акселераторов и венчурных фондов, '
            'в воскресенье — финальные питчи перед жюри. Победители получают инвестиции до 3 млн ₽ '
            'и место в акселераторе.'
        ),
        'location': 'HubMoscow, Москва',
        'format': Event.Format.OFFLINE,
        'categories': ['startup', 'networking'],
        'access_type': 'open',
        'reg_opens': 0,
        'reg_closes': 68,
        'event_starts': 70,
        'event_ends': 72,
    },
]


class Command(BaseCommand):
    help = 'Seed test events and organizations into the database'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Delete existing seed data before creating')

    def handle(self, *args, **options):
        if options['clear']:
            org_names = [d['org_name'] for d in SEED_DATA]
            deleted_orgs, _ = Organization.objects.filter(name__in=org_names).delete()
            self.stdout.write(f'Deleted {deleted_orgs} organizations (and their events)')

        now = timezone.now()
        created_events = 0
        created_orgs = 0

        for data in SEED_DATA:
            org, org_created = Organization.objects.get_or_create(
                name=data['org_name'],
                defaults={'description': f'Организация {data["org_name"]}'},
            )
            if org_created:
                created_orgs += 1

            event, event_created = Event.objects.get_or_create(
                title=data['title'],
                organization=org,
                defaults={
                    'description':        data['description'],
                    'location':           data['location'],
                    'format':             data['format'],
                    'categories':         data['categories'],
                    'access_type':        data['access_type'],
                    'is_published':       True,
                    'registration_start': now + timedelta(days=data['reg_opens']),
                    'registration_end':   now + timedelta(days=data['reg_closes']),
                    'event_start':        now + timedelta(days=data['event_starts']),
                    'event_end':          now + timedelta(days=data['event_ends']),
                },
            )
            if event_created:
                created_events += 1
            else:
                # Update categories/access_type for existing events that predate the new fields
                if not event.categories:
                    event.categories = data['categories']
                    event.access_type = data['access_type']
                    event.save(update_fields=['categories', 'access_type'])
                self.stdout.write(f'  already exists: {data["title"]}')

        self.stdout.write(self.style.SUCCESS(
            f'Done: {created_orgs} organizations, {created_events} events created.'
        ))
