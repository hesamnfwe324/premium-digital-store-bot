from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import settings
from bot.utils.logger import logger


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.db_url,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=1800,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def _seed_premium_services(session):
    from database.models import Product, ProductCategory, ProductType
    products = [
        Product(name="VPN پریمیوم ۱ ماهه", name_en="VPN Premium 1 Month", name_fa="VPN پریمیوم ۱ ماهه",
                description="دسترسی نامحدود با VPN پریمیوم", description_en="Unlimited access with premium VPN",
                category=ProductCategory.PREMIUM_SERVICE, product_type=ProductType.PREMIUM_SERVICE,
                price=4.0, price_usdt=4.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=1),
        Product(name="اسپاتیفای پریمیوم ۱ ماهه", name_en="Spotify Premium 1 Month", name_fa="اسپاتیفای پریمیوم ۱ ماهه",
                description="موسیقی بی‌محدود بدون تبلیغ", description_en="Unlimited music without ads",
                category=ProductCategory.PREMIUM_SERVICE, product_type=ProductType.PREMIUM_SERVICE,
                price=6.0, price_usdt=6.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=2),
        Product(name="یوتیوب پریمیوم ۱ ماهه", name_en="YouTube Premium 1 Month", name_fa="یوتیوب پریمیوم ۱ ماهه",
                description="ویدیو بدون تبلیغ + YouTube Music", description_en="Ad-free videos + YouTube Music",
                category=ProductCategory.PREMIUM_SERVICE, product_type=ProductType.PREMIUM_SERVICE,
                price=7.0, price_usdt=7.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=3),
        Product(name="نتفلیکس بیسیک ۱ ماهه", name_en="Netflix Basic 1 Month", name_fa="نتفلیکس بیسیک ۱ ماهه",
                description="استریم نامحدود — ۱ صفحه", description_en="Unlimited streaming — 1 screen",
                category=ProductCategory.PREMIUM_SERVICE, product_type=ProductType.PREMIUM_SERVICE,
                price=8.0, price_usdt=8.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=4),
        Product(name="دیسکورد نیترو ۱ ماهه", name_en="Discord Nitro 1 Month", name_fa="دیسکورد نیترو ۱ ماهه",
                description="آپلود بزرگ، ایموجی سفارشی و سرور بوست", description_en="Larger uploads, custom emoji & server boosts",
                category=ProductCategory.PREMIUM_SERVICE, product_type=ProductType.PREMIUM_SERVICE,
                price=9.0, price_usdt=9.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=5),
        Product(name="نتفلیکس استاندارد ۱ ماهه", name_en="Netflix Standard 1 Month", name_fa="نتفلیکس استاندارد ۱ ماهه",
                description="استریم نامحدود — ۲ صفحه Full HD", description_en="Unlimited streaming — 2 screens Full HD",
                category=ProductCategory.PREMIUM_SERVICE, product_type=ProductType.PREMIUM_SERVICE,
                price=12.0, price_usdt=12.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=6),
        Product(name="آفیس ۳۶۵ پرسونال ۱ ماهه", name_en="Office 365 Personal 1 Month", name_fa="آفیس ۳۶۵ پرسونال ۱ ماهه",
                description="Word، Excel، PowerPoint + OneDrive 1TB", description_en="Word, Excel, PowerPoint & 1TB OneDrive",
                category=ProductCategory.PREMIUM_SERVICE, product_type=ProductType.PREMIUM_SERVICE,
                price=14.0, price_usdt=14.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=7),
        Product(name="ادوبی کریتیو کلود ۱ ماهه", name_en="Adobe Creative Cloud 1 Month", name_fa="ادوبی کریتیو کلود ۱ ماهه",
                description="Photoshop، Illustrator، Premiere و همه اپ‌های ادوبی", description_en="Photoshop, Illustrator, Premiere & all Adobe apps",
                category=ProductCategory.PREMIUM_SERVICE, product_type=ProductType.PREMIUM_SERVICE,
                price=18.0, price_usdt=18.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=8),
        Product(name="نتفلیکس استاندارد ۳ ماهه", name_en="Netflix Standard 3 Months", name_fa="نتفلیکس استاندارد ۳ ماهه",
                description="۳ ماه استریم — ۲ صفحه Full HD", description_en="3 months streaming — 2 screens Full HD",
                category=ProductCategory.PREMIUM_SERVICE, product_type=ProductType.PREMIUM_SERVICE,
                price=30.0, price_usdt=30.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=9),
        Product(name="یوتیوب پریمیوم ۶ ماهه", name_en="YouTube Premium 6 Months", name_fa="یوتیوب پریمیوم ۶ ماهه",
                description="۶ ماه بدون تبلیغ + YouTube Music", description_en="6 months ad-free + YouTube Music",
                category=ProductCategory.PREMIUM_SERVICE, product_type=ProductType.PREMIUM_SERVICE,
                price=38.0, price_usdt=38.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=10),
    ]
    session.add_all(products)
    await session.commit()
    logger.info(f"✅ Seeded {len(products)} premium service products")


async def _seed_gift_cards(session):
    from database.models import Product, ProductCategory, ProductType
    products = [
        Product(name="گیفت کارت گوگل پلی $5", name_en="Google Play $5 Gift Card", name_fa="گیفت کارت گوگل پلی $5",
                description="گیفت کارت رسمی Google Play", description_en="Official Google Play gift card — $5",
                category=ProductCategory.GIFT_CARD, product_type=ProductType.GIFT_CARD,
                price=5.5, price_usdt=5.5, quantity=999, delivery_time="Instant", is_active=True, sort_order=11, gift_card_brand="Google Play"),
        Product(name="گیفت کارت اپل $5", name_en="Apple/iTunes $5 Gift Card", name_fa="گیفت کارت اپل $5",
                description="گیفت کارت رسمی App Store / iTunes", description_en="Official App Store gift card — $5",
                category=ProductCategory.GIFT_CARD, product_type=ProductType.GIFT_CARD,
                price=5.5, price_usdt=5.5, quantity=999, delivery_time="Instant", is_active=True, sort_order=12, gift_card_brand="iTunes"),
        Product(name="گیفت کارت آمازون $10", name_en="Amazon $10 Gift Card", name_fa="گیفت کارت آمازون $10",
                description="گیفت کارت رسمی Amazon.com", description_en="Official Amazon.com gift card — $10",
                category=ProductCategory.GIFT_CARD, product_type=ProductType.GIFT_CARD,
                price=11.0, price_usdt=11.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=13, gift_card_brand="Amazon"),
        Product(name="گیفت کارت گوگل پلی $10", name_en="Google Play $10 Gift Card", name_fa="گیفت کارت گوگل پلی $10",
                description="گیفت کارت رسمی Google Play", description_en="Official Google Play gift card — $10",
                category=ProductCategory.GIFT_CARD, product_type=ProductType.GIFT_CARD,
                price=11.0, price_usdt=11.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=14, gift_card_brand="Google Play"),
        Product(name="گیفت کارت استیم $10", name_en="Steam $10 Gift Card", name_fa="گیفت کارت استیم $10",
                description="گیفت کارت رسمی Steam", description_en="Official Steam gift card — $10",
                category=ProductCategory.GIFT_CARD, product_type=ProductType.GIFT_CARD,
                price=11.0, price_usdt=11.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=15, gift_card_brand="Steam"),
        Product(name="گیفت کارت اپل $10", name_en="Apple/iTunes $10 Gift Card", name_fa="گیفت کارت اپل $10",
                description="گیفت کارت رسمی App Store / iTunes", description_en="Official App Store gift card — $10",
                category=ProductCategory.GIFT_CARD, product_type=ProductType.GIFT_CARD,
                price=11.0, price_usdt=11.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=16, gift_card_brand="iTunes"),
        Product(name="گیفت کارت پلی‌استیشن $20", name_en="PlayStation $20 Gift Card", name_fa="گیفت کارت پلی‌استیشن $20",
                description="گیفت کارت رسمی PlayStation Store", description_en="Official PlayStation Store gift card — $20",
                category=ProductCategory.GIFT_CARD, product_type=ProductType.GIFT_CARD,
                price=21.0, price_usdt=21.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=17, gift_card_brand="PlayStation"),
        Product(name="گیفت کارت ایکس‌باکس $20", name_en="Xbox $20 Gift Card", name_fa="گیفت کارت ایکس‌باکس $20",
                description="گیفت کارت رسمی Xbox / Microsoft Store", description_en="Official Xbox gift card — $20",
                category=ProductCategory.GIFT_CARD, product_type=ProductType.GIFT_CARD,
                price=21.0, price_usdt=21.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=18, gift_card_brand="Xbox"),
        Product(name="گیفت کارت آمازون $25", name_en="Amazon $25 Gift Card", name_fa="گیفت کارت آمازون $25",
                description="گیفت کارت رسمی Amazon.com", description_en="Official Amazon.com gift card — $25",
                category=ProductCategory.GIFT_CARD, product_type=ProductType.GIFT_CARD,
                price=26.0, price_usdt=26.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=19, gift_card_brand="Amazon"),
        Product(name="گیفت کارت استیم $50", name_en="Steam $50 Gift Card", name_fa="گیفت کارت استیم $50",
                description="گیفت کارت رسمی Steam", description_en="Official Steam gift card — $50",
                category=ProductCategory.GIFT_CARD, product_type=ProductType.GIFT_CARD,
                price=52.0, price_usdt=52.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=20, gift_card_brand="Steam"),
        Product(name="گیفت کارت آمازون $50", name_en="Amazon $50 Gift Card", name_fa="گیفت کارت آمازون $50",
                description="گیفت کارت رسمی Amazon.com", description_en="Official Amazon.com gift card — $50",
                category=ProductCategory.GIFT_CARD, product_type=ProductType.GIFT_CARD,
                price=52.0, price_usdt=52.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=21, gift_card_brand="Amazon"),
        Product(name="گیفت کارت پلی‌استیشن $50", name_en="PlayStation $50 Gift Card", name_fa="گیفت کارت پلی‌استیشن $50",
                description="گیفت کارت رسمی PlayStation Store", description_en="Official PlayStation Store gift card — $50",
                category=ProductCategory.GIFT_CARD, product_type=ProductType.GIFT_CARD,
                price=53.0, price_usdt=53.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=22, gift_card_brand="PlayStation"),
        Product(name="گیفت کارت ایکس‌باکس $50", name_en="Xbox $50 Gift Card", name_fa="گیفت کارت ایکس‌باکس $50",
                description="گیفت کارت رسمی Xbox / Microsoft Store", description_en="Official Xbox gift card — $50",
                category=ProductCategory.GIFT_CARD, product_type=ProductType.GIFT_CARD,
                price=53.0, price_usdt=53.0, quantity=999, delivery_time="Instant", is_active=True, sort_order=23, gift_card_brand="Xbox"),
    ]
    session.add_all(products)
    await session.commit()
    logger.info(f"✅ Seeded {len(products)} gift card products")


async def seed_products():
    from sqlalchemy import select, func
    from database.models import Product, ProductCategory

    async with AsyncSessionLocal() as session:
        for category, seeder in [
            (ProductCategory.PREMIUM_SERVICE, _seed_premium_services),
            (ProductCategory.GIFT_CARD, _seed_gift_cards),
        ]:
            result = await session.execute(
                select(func.count()).select_from(Product).where(Product.category == category)
            )
            count = result.scalar() or 0
            if count == 0:
                await seeder(session)
            else:
                logger.info(f"⏭️ Skipping {category.value} seed — {count} already exist")


async def init_db():
    from database.models import (
        User, Product, Order, Payment, Wallet, Transaction,
        GiftCard, VisaCard, MasterCard, Ticket, Referral,
        DiscountCode, Setting, Language
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database initialized successfully")
    await seed_products()
