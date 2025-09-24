import json
import logging
import os
import uuid
from datetime import datetime
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, ConfigDict, Field


ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(ROOT_DIR / ".env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is not set")
    return value


# MongoDB connection
mongo_url = _require_env("MONGO_URL")
client = AsyncIOMotorClient(mongo_url)
db = client[_require_env("DB_NAME")]

WEBHOOK_REDIRECT_URL = os.getenv("WEBHOOK_REDIRECT_URL")
WEBHOOK_VERIFICATION_STATE_ID = "webhook_verification"

webhook_state_collection = db["webhook_state"]
webhook_events_collection = db["webhook_events"]


# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Models
class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    shortDescription: str
    fullDescription: str
    price: int
    deliveryTime: str
    icon: str
    imageUrl: str | None = None
    features: List[str]
    technologies: List[str]
    category: str


class CartItem(BaseModel):
    product_id: str
    quantity: int


class Cart(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    items: List[CartItem]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WebhookPayload(BaseModel):
    """Гибкая модель для входящих webhook-событий."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    event_type: str | None = Field(default=None, alias="eventType")


class WebhookProcessResult(BaseModel):
    status: str = "ok"
    saved_event_id: str


class WebhookVerificationStatus(BaseModel):
    """Состояние прохождения проверки вебхука."""

    verified: bool
    verified_at: datetime | None = None


# QR codes data for different banks and amounts
QR_CODES = {
    "sovcombank": {
        500: "https://qr.nspk.ru/AD200035F0DUH05G8CTO9TU18246VMSC?type=02&bank=100000000013&sum=50000&cur=RUB&crc=8FC7",
        1000: "https://qr.nspk.ru/AD20001SUJS2BNVC8JQPQ47P7UHLEN8D?type=02&bank=100000000013&sum=100000&cur=RUB&crc=03CF",
        1500: "https://qr.nspk.ru/BD200027AGDORBUU9LNOKG3RHNJVJ36C?type=02&bank=100000000013&sum=150000&cur=RUB&crc=B501",
        2000: "https://qr.nspk.ru/AD20005ESSIHKG3U846PN75EISQUVSN0?type=02&bank=100000000013&sum=200000&cur=RUB&crc=75CE",
        2500: "https://qr.nspk.ru/AD2000283T1SCG1M8JC9265SFAHMBREI?type=02&bank=100000000013&sum=250000&cur=RUB&crc=E079",
        3000: "https://qr.nspk.ru/AD20003EHA4GJ8V98Q5B0M5FAP2QIUHH?type=02&bank=100000000013&sum=300000&cur=RUB&crc=8E32",
        3500: "https://qr.nspk.ru/BD20003S0FMJIBBF8F5PF6EJ3N2V22UF?type=02&bank=100000000013&sum=350000&cur=RUB&crc=92E5",
        4000: "https://qr.nspk.ru/AD200014770NKLJV9LPOA6HENSQFF70S?type=02&bank=100000000013&sum=400000&cur=RUB&crc=CAA4",
        4500: "https://qr.nspk.ru/AD200010J8SM00P98EBOD1K3A98KRR62?type=02&bank=100000000013&sum=450000&cur=RUB&crc=2A81",
        5000: "https://qr.nspk.ru/BD20001ECKRBFK6J8KMOP6BHMTCLU83D?type=02&bank=100000000013&sum=500000&cur=RUB&crc=E03C",
        5500: "https://qr.nspk.ru/BD20004CHNJ4NO3V8P8QJR96Q543OD91?type=02&bank=100000000013&sum=550000&cur=RUB&crc=861D",
        6000: "https://qr.nspk.ru/BD20002FONGUA01V90OOOI6R2E88JI2S?type=02&bank=100000000013&sum=600000&cur=RUB&crc=D2FD",
        6500: "https://qr.nspk.ru/BD20001L9DGM854A9M2BHIDCNT8ENQOM?type=02&bank=100000000013&sum=650000&cur=RUB&crc=7EB6",
        7000: "https://qr.nspk.ru/BD20000KFB69F9L49SO8DQFKRD6UF5ED?type=02&bank=100000000013&sum=700000&cur=RUB&crc=AEAA",
        7500: "https://qr.nspk.ru/BD2000044JK2M8408E68SR2G979D998H?type=02&bank=100000000013&sum=750000&cur=RUB&crc=C532",
        8000: "https://qr.nspk.ru/BD20003JN7OE7RQE8PN8T0P0QL2UF249?type=02&bank=100000000013&sum=800000&cur=RUB&crc=8044",
        8500: "https://qr.nspk.ru/BD200008LQ4MIKAN9VSP3QIMASH1N8BV?type=02&bank=100000000013&sum=850000&cur=RUB&crc=C3F2",
        9000: "https://qr.nspk.ru/BD200037VI5M70MK8CN86N47MDFVVVTE?type=02&bank=100000000013&sum=900000&cur=RUB&crc=59FA",
        9500: "https://qr.nspk.ru/BD20007QONN27TLA8Q2R1P3SJLAMKOMA?type=02&bank=100000000013&sum=950000&cur=RUB&crc=B049",
        10000: "https://qr.nspk.ru/AD20006SSC2J4ALS8JNAOPS8VBV5QR3M?type=02&bank=100000000013&sum=1000000&cur=RUB&crc=1590",
        10500: "https://qr.nspk.ru/BD2000102GPB37QV93BRTPLFVCUPN5AS?type=02&bank=100000000013&sum=1050000&cur=RUB&crc=78D0",
        11000: "https://qr.nspk.ru/AD20003QCCDTM1VS9CPPVP4FR72P9SMH?type=02&bank=100000000013&sum=1100000&cur=RUB&crc=9A5F",
        11500: "https://qr.nspk.ru/AD200072B49SO4AP8NM8PEINO2E9CV5H?type=02&bank=100000000013&sum=1150000&cur=RUB&crc=6F1E",
        12000: "https://qr.nspk.ru/BD20001460E5AQBA8RRPVNF27SVUH1SM?type=02&bank=100000000013&sum=1200000&cur=RUB&crc=2FA4",
        12500: "https://qr.nspk.ru/BD20005R5C9ML69B9J5OQO79FRDUMJMJ?type=02&bank=100000000013&sum=1250000&cur=RUB&crc=41F4",
        13000: "https://qr.nspk.ru/BD20002C2UF9L57595JBL1TP62ISQ4DR?type=02&bank=100000000013&sum=1300000&cur=RUB&crc=32EE",
        13500: "https://qr.nspk.ru/AD20007EE3SIROEQ8ASRRFR8E4FOO367?type=02&bank=100000000013&sum=1350000&cur=RUB&crc=9A78",
        14000: "https://qr.nspk.ru/BD20000PCCBRE7I48EDBFIHS0SC6GH07?type=02&bank=100000000013&sum=1400000&cur=RUB&crc=75DA",
        14500: "https://qr.nspk.ru/BD20005KU77LQ8PC9P5ACJECTK3L1N0L?type=02&bank=100000000013&sum=1450000&cur=RUB&crc=1291",
        15000: "https://qr.nspk.ru/BD200024M6T0A91L89BBC00E9SORJU59?type=02&bank=100000000013&sum=1500000&cur=RUB&crc=A9CE",
        16000: "https://qr.nspk.ru/BD20004Q8LU5SPE48TUAPJN0CNADVKFF?type=02&bank=100000000013&sum=1600000&cur=RUB&crc=F216",
        17000: "https://qr.nspk.ru/BD20004N5AEGLP808B68A2C68U2UEA29?type=02&bank=100000000013&sum=1700000&cur=RUB&crc=0122",
        18000: "https://qr.nspk.ru/BD200064OGJMLDSR8PG9EF0J7H9C29T5?type=02&bank=100000000013&sum=1800000&cur=RUB&crc=5695",
        19000: "https://qr.nspk.ru/AD20003DU28GCHVF9AEOE7VL6TQEHKCR?type=02&bank=100000000013&sum=1900000&cur=RUB&crc=E1B8",
        20000: "https://qr.nspk.ru/AD20007VQNBVL0L09GBQB98BKP8T5RBV?type=02&bank=100000000013&sum=2000000&cur=RUB&crc=1A95",
        25000: "https://qr.nspk.ru/AD20007KVNVO0AD085MBNFSFI51KQED3?type=02&bank=100000000013&sum=2500000&cur=RUB&crc=F435",
        30000: "https://qr.nspk.ru/BD2000092NBTIPG79QDON0A7HVG2MG4N?type=02&bank=100000000013&sum=3000000&cur=RUB&crc=EAA8",
        35000: "https://qr.nspk.ru/BD200074ICL732SD9R68BGKSVI79CJ10?type=02&bank=100000000013&sum=3500000&cur=RUB&crc=6F9B",
        40000: "https://qr.nspk.ru/AD20000IQ8NI6QFA8MFBGJK2P25KSV2S?type=02&bank=100000000013&sum=4000000&cur=RUB&crc=DECA",
        45000: "https://qr.nspk.ru/AD20003ASB5IM32H8HI9NIO0E400BE52?type=02&bank=100000000013&sum=4500000&cur=RUB&crc=CD4C",
        50000: "https://qr.nspk.ru/AD200047UPA31SRG8LGPVNMB6DOH4QRA?type=02&bank=100000000013&sum=5000000&cur=RUB&crc=FEA3"
    },
    "sber": {
        500: "https://b2b.cbrpay.ru/AS2B003EO04CPDQC9UE94HBVHFN6JJ7I",
        1000: "https://b2b.cbrpay.ru/AS2B001EJU9ICOR482KB5FQKK7AUG8Q5",
        1500: "https://b2b.cbrpay.ru/AS2B0007NT2VTOPA8IIBA67ISLE9C58D",
        2000: "https://b2b.cbrpay.ru/AS2B002DGOVF1PIF8VHAC43JDBMF5MVO",
        2500: "https://b2b.cbrpay.ru/AS2B001KEL5RCAAN8PIQDN4HCNPKLHUS",
        3000: "https://b2b.cbrpay.ru/AS2B00396N0DM6OR9C4B6CG7E5I13TM7",
        3500: "https://b2b.cbrpay.ru/AS2B002AE865QOOG82SB51SG3RKG27FN",
        4000: "https://b2b.cbrpay.ru/AS2B0016GSLE5F3S8GUPTEI5J8SSA0UF",
        4500: "https://b2b.cbrpay.ru/AS2B003BP5COV7118MTO9DFN6D4D2DER",
        5000: "https://b2b.cbrpay.ru/AS2B0066AHIJ9D3M9FQRGINAD9C0QJNR",
        5500: "https://b2b.cbrpay.ru/AS2B0046045VNPSE9S5OH4VL1G7JBNLG",
        6000: "https://b2b.cbrpay.ru/AS2B004FV1KHOROO8KER2TF3CF76AT7D",
        6500: "https://b2b.cbrpay.ru/AS2B002KKCLS5ESP9V2R7JA0CT8R0D6A",
        7000: "https://b2b.cbrpay.ru/AS2B000H0DS7O8KP80KQ4AU37U3MMOE4",
        7500: "https://b2b.cbrpay.ru/AS2B000C5LFHRHQT8UHPU74U2CV1BGPF",
        8000: "https://b2b.cbrpay.ru/AS2B001VU749H5PL903RUDC8F03LTA2F",
        8500: "https://b2b.cbrpay.ru/AS2B0037LAUP1G5J8R6OISMFF5F8J446",
        9000: "https://b2b.cbrpay.ru/AS2B00758FHDODMT9UVO97V0G96MML1I",
        9500: "https://b2b.cbrpay.ru/AS2B006S245B11LE8SRQ2O0C751NSREF",
        10000: "https://b2b.cbrpay.ru/AS2B004CVK5B76CS81IBHOF01FHSFVTC",
        10500: "https://b2b.cbrpay.ru/AS2B007G22KR2N7U9CJ8825R6U9O4FGK",
        11000: "https://b2b.cbrpay.ru/AS2B002Q670QCK0292V8RAMK34V37VSE",
        11500: "https://b2b.cbrpay.ru/AS2B007P7AAHIJNJ97FP8TK4K84P5G95",
        12000: "https://b2b.cbrpay.ru/AS2B001IG49BFIGO8P9A75J2K1LTBNQP",
        12500: "https://b2b.cbrpay.ru/AS2B0018JCGV1I24954AB826JERBBV0A",
        13000: "https://b2b.cbrpay.ru/AS2B003M31JAJ1579F7OMT8Q5LBTSI6C",
        13500: "https://b2b.cbrpay.ru/AS2B004TKQEU8B8G9J4RQ1754QQU93LN",
        14000: "https://b2b.cbrpay.ru/AS2B0077SS131JTG9VMBTFHH4NUHO7FJ",
        14500: "https://b2b.cbrpay.ru/AS2B0011B1C8C1JF92AQRCTI61KKBTGA",
        15000: "https://b2b.cbrpay.ru/AS2B002CNLVRIARR9HIANGA7NRVP7QQQ",
        16000: "https://b2b.cbrpay.ru/AS2B00638S6FOHMH9UT8U0P65SFPCUR8",
        17000: "https://b2b.cbrpay.ru/AS2B0028QOB4M4DO8SV9B5HT41D2R6BA",
        18000: "https://b2b.cbrpay.ru/AS2B007V9AMHDJDR898OFREK8L79AMA5",
        19000: "https://b2b.cbrpay.ru/AS2B0061T14PP0C89IGPD0HFHGRB1RH2",
        20000: "https://b2b.cbrpay.ru/AS2B0014P10SKBUL9SDA24OMFODQFF8H",
        25000: "https://b2b.cbrpay.ru/AS2B003U5618RV5B882QNC8MGV4F9H9C",
        30000: "https://b2b.cbrpay.ru/AS2B00192MTUDK2P83V8HP7GI9JTJH34",
        35000: "https://b2b.cbrpay.ru/AS2B001OMT1HS0EC8IRPLDESUAMHHIGA",
        40000: "https://b2b.cbrpay.ru/AS2B005AE5FP5297868BQ16D777QJ68P",
        45000: "https://b2b.cbrpay.ru/AS2B003IHAKLMOCU8FEO5K1MD9K2RIL3",
        50000: "https://b2b.cbrpay.ru/AS2B002JJJISCA7Q8A4PG4LQSTGRNTNC"
    },
    "vtb": {
        500: "https://b2b.cbrpay.ru/AS2B0044B1P73FAH8JE97DEFN80JEGQR",
        1000: "https://b2b.cbrpay.ru/AS2B002P6HDIQQEE94L9U1MMTU420UGG",
        1500: "https://b2b.cbrpay.ru/AS2B00790ASFMOBI90LRV8DAPS6E9B53",
        2000: "https://b2b.cbrpay.ru/AS2B002S5FEFJ4NM9D8Q7M5PGA1VPR9I",
        2500: "https://b2b.cbrpay.ru/BS2B004H9I2NEFK280IRIVNVGK8O8QVL",
        3000: "https://b2b.cbrpay.ru/BS2B005E6QHCPQ429FU8M2EH4CUPGG83",
        3500: "https://b2b.cbrpay.ru/BS2B0009CR5NPV3H95JPHCFMGGI35CP9",
        4000: "https://b2b.cbrpay.ru/AS2B005JISMST5O38NURH7VKC9RCBDQ6",
        4500: "https://b2b.cbrpay.ru/BS2B00181B9VP6RP88EPONR55CV70KMP",
        5000: "https://b2b.cbrpay.ru/AS2B005GL2G7NFC38ETQOPF8ELI1KKPP",
        5500: "https://b2b.cbrpay.ru/AS2B003J70EL9T8U955BHDVRAMQ2Q88S",
        6000: "https://b2b.cbrpay.ru/BS2B00319CDBR3J28ULRCDUN702CADTR",
        6500: "https://b2b.cbrpay.ru/BS2B006VCOVG3U9097SO8LA8IIU21PTM",
        7000: "https://b2b.cbrpay.ru/AS2B003T1HM4IJIR81A8I8B17T4I8SJI",
        7500: "https://b2b.cbrpay.ru/AS2B002H2ER9P60293BQ5E024ISC27CJ",
        8000: "https://b2b.cbrpay.ru/AS2B000OR6F6LLG09EMB5IN8PLF1TEPA",
        8500: "https://b2b.cbrpay.ru/AS2B003L17RU8QJ38D0QFR0PCEQCDAU4",
        9000: "https://b2b.cbrpay.ru/BS2B003GG852C5OF8BNRITH7AN70I1UB",
        9500: "https://b2b.cbrpay.ru/BS2B000J4HKRM51T85R99IO4JOJV4G0C",
        10000: "https://b2b.cbrpay.ru/AS2B000N2NVEUQPI86UB38A5OOT82AKO",
        10500: "https://b2b.cbrpay.ru/BS2B004DDQCMF6HJ90HOV9OBOJ9TE8EL",
        11000: "https://b2b.cbrpay.ru/AS2B0035R4O978GQ8EG91RTADQ21PFGM",
        11500: "https://b2b.cbrpay.ru/AS2B0072AE066UMG931P4OPHIF6PN2D2",
        12000: "https://b2b.cbrpay.ru/BS2B005GMBNSAD3P9Q4ARJOTV0P7N9V2",
        12500: "https://b2b.cbrpay.ru/AS2B004G4RNDAAKB8JD86OIUOVEQ5UAU",
        13000: "https://b2b.cbrpay.ru/BS2B0013ECPP2HTD8A28HB2DA2OIUCH7",
        13500: "https://b2b.cbrpay.ru/BS2B000UGM22ATRK8459CO6FAQ1Q69K7",
        14000: "https://b2b.cbrpay.ru/AS2B001U5NT750KA8C6ORD3OFPT5P9RQ",
        14500: "https://b2b.cbrpay.ru/AS2B005UG5CU81JG9A5Q52RLD90Q39HH",
        15000: "https://b2b.cbrpay.ru/BS2B00610MGSLA0L9HEO8VEMNDMOQ0RB",
        16000: "https://b2b.cbrpay.ru/BS2B007UQLD59IBT90VBGAJAM7JPARUA",
        17000: "https://b2b.cbrpay.ru/BS2B000N0G43EC929V0B3NRRVK4LKLQO",
        18000: "https://b2b.cbrpay.ru/AS2B0006OKLUL8H19DSA5GV9C258S0UJ",
        19000: "https://b2b.cbrpay.ru/AS2B002TBNFT5SOF80QBA09HNAJ5R4A7",
        20000: "https://b2b.cbrpay.ru/BS2B002HG8T9RP519L7A0E2HCDR8EDIT",
        25000: "https://b2b.cbrpay.ru/BS2B00614BC3P02C8IPA1CKVJF32C3NF",
        30000: "https://b2b.cbrpay.ru/AS2B0051AA1D1J5J9OB8T2O7S1EV27CA",
        35000: "https://b2b.cbrpay.ru/AS2B0009R9LHNTC88NOBL0LTUQC4RTTN",
        40000: "https://b2b.cbrpay.ru/BS2B0073SSON68VV8D9O56UGMGGP25HV",
        45000: "https://b2b.cbrpay.ru/BS2B002M0FS1IT7P8599OHV06780BC70",
        50000: "https://b2b.cbrpay.ru/AS2B001BQ78EI0AO8LIA7FVD1PR86B9F"
    },
    "tbank": {
        500: "https://b2b.cbrpay.ru/AS2B004QSVRARGL690AOACJUOEFPCUMF",
        1000: "https://b2b.cbrpay.ru/BS2B005AHRPESB6783OQ5EL1016T9SEK",
        1500: "https://b2b.cbrpay.ru/AS2B006T2052OUDO8LGO452NESHHHO9B",
        2000: "https://b2b.cbrpay.ru/AS2B002RQJMNQ92J9E3B6VOJRMB9HG3P",
        2500: "https://b2b.cbrpay.ru/BS2B0053GLAETCR69PVQR9NKNBS0OLS9",
        3000: "https://b2b.cbrpay.ru/AS2B00610LB6C9LJ9KLBC84HUCTT4N62",
        3500: "https://b2b.cbrpay.ru/BS2B001BKU84V2H99VQQ448H764O94DV",
        4000: "https://b2b.cbrpay.ru/BS2B007UMADOE5IP8C99D31MA4918440",
        4500: "https://b2b.cbrpay.ru/AS2B0078B1OR8GQN92EPQ58I80V62T1S",
        5000: "https://b2b.cbrpay.ru/AS2B001IQJ7I36238RHA7DJO4EH3QMUU",
        5500: "https://b2b.cbrpay.ru/BS2B002CNVL30U2G8K1PV6360V2U3J4N",
        6000: "https://b2b.cbrpay.ru/BS2B002NDVOKHR3486B8INKF6RE439PA",
        6500: "https://b2b.cbrpay.ru/AS2B007LTONB5ONK9FCO2HE1I0QO5VAA",
        7000: "https://b2b.cbrpay.ru/BS2B001KQN192QGI95GBRI9COCQAIT9O",
        7500: "https://b2b.cbrpay.ru/BS2B0016TA0G143L8NNO9VKAT0CTUEUF",
        8000: "https://b2b.cbrpay.ru/BS2B000RNPIB3Q3P8589GK9N9NUKPJ9K",
        8500: "https://b2b.cbrpay.ru/AS2B002EJ25U7Q2D9RDB9IRBJ9DC4CIJ",
        9000: "https://b2b.cbrpay.ru/AS2B001101027E7J912QIBBHVVLFR10I",
        9500: "https://b2b.cbrpay.ru/AS2B005QPQAI70888MVPN51ICEQSKO43",
        10000: "https://b2b.cbrpay.ru/BS2B002U9HTIL3VA8N19KG10A1DJK77T",
        10500: "https://b2b.cbrpay.ru/AS2B0000MUUBIPLF8B98I9JK8872VIIB",
        11000: "https://b2b.cbrpay.ru/BS2B00457CVM5EV792JQTSFV6IQPJR3M",
        11500: "https://b2b.cbrpay.ru/AS2B000I4I7D7PAA87S8OFNOUCGB5NNQ",
        12000: "https://b2b.cbrpay.ru/AS2B005FCJ18550G940B9M969V4GV75N",
        12500: "https://b2b.cbrpay.ru/BS2B0043OMMIGM7G9IFB08UKT3HB5QVE",
        13000: "https://b2b.cbrpay.ru/BS2B001NFM16C36S8UVAIPFQFF9JA2BH",
        13500: "https://b2b.cbrpay.ru/AS2B007QADPPACBO9HQB5DN24AH3LRF5",
        14000: "https://b2b.cbrpay.ru/AS2B007QADPPACBO9HQB5DN24AH3LRF5",
        14500: "https://b2b.cbrpay.ru/BS2B0064P1FEDGS984RQFH0IBQPM18P8",
        15000: "https://b2b.cbrpay.ru/AS2B004KRPSQNJO59Q9P3P4K7B9Q4LQ1",
        16000: "https://b2b.cbrpay.ru/AS2B0030GM0LF9LQ9RARDG7H4205D5VB",
        17000: "https://b2b.cbrpay.ru/AS2B003QBKUDFG3B8LI9LK10HM6OUHBC",
        18000: "https://b2b.cbrpay.ru/BS2B003BG3E2TGNU84A8HI1R8H97BJ9I",
        19000: "https://b2b.cbrpay.ru/BS2B001MNPMNA39I8RFQQVFEMTUJ84NG",
        20000: "https://b2b.cbrpay.ru/AS2B003686HKA12T8F9R3527GMV6GJH9",
        25000: "https://b2b.cbrpay.ru/BS2B002J2KKDVS5I9MA86FC0P03BO7E0",
        30000: "https://b2b.cbrpay.ru/AS2B002Q8QT5GMPR8F4RTTCEVQ7L6NS3",
        35000: "https://b2b.cbrpay.ru/BS2B001FM5QOPQU88T5832M4SNRDHP4F",
        40000: "https://b2b.cbrpay.ru/BS2B0041J3PK0KTS8JSO1NM1ML3C8AFT",
        45000: "https://b2b.cbrpay.ru/AS2B007J5IQ04S1L85H929R2UN1496UK",
        50000: "https://b2b.cbrpay.ru/AS2B001LSRACR5GS99AB47GNCNDA94F9"
    }
}

BANKS = {
    "sovcombank": {"name": "Совкомбанк", "icon": "🏦"},
    "sber": {"name": "Сбер", "icon": "💚"},
    "vtb": {"name": "ВТБ", "icon": "🔵"},
    "tbank": {"name": "Т-Банк", "icon": "⚡"}
}


def get_qr_code(bank: str, amount: int) -> str:
    """Get QR code URL for specific bank and amount"""
    if bank in QR_CODES and amount in QR_CODES[bank]:
        return QR_CODES[bank][amount]
    return None


# Sample products data with correct pricing
PRODUCTS_DATA = [
    {
            "name": "Простая HTML страница",
            "shortDescription": "Базовая HTML страница с минимальным дизайном",
            "fullDescription": "Создание простой HTML страницы с базовым дизайном и основной информацией о компании. Подходит для быстрого старта онлайн присутствия.",
            "price": 500,
            "deliveryTime": "1-2 дня",
            "icon": "📄",
            "imageUrl": "https://static.tildacdn.com/tild3262-3039-4939-b361-663935326330/20250719_0357____sim.png",
            "features": ["HTML разметка", "Базовые стили", "Контактная информация"],
            "technologies": ["HTML5", "CSS3"],
            "category": "Веб-разработка"
        },
        {
            "name": "Визитка сайт",
            "shortDescription": "Простой сайт-визитка для малого бизнеса",
            "fullDescription": "Разработка сайта-визитки с информацией о компании, услугах и контактами. Включает адаптивный дизайн и базовую SEO оптимизацию.",
            "price": 1000,
            "deliveryTime": "1-2 дня",
            "icon": "💼",
            "imageUrl": "https://static.tildacdn.com/tild6464-3166-4562-b363-343633623532/20250719_0358____sim.png",
            "features": ["О компании", "Услуги", "Контакты", "Адаптивный дизайн"],
            "technologies": ["HTML5", "CSS3", "JavaScript"],
            "category": "Веб-разработка"
        },
        {
            "name": "Лендинг с формой",
            "shortDescription": "Лендинг страница с формой обратной связи",
            "fullDescription": "Создание лендинг страницы с призывом к действию и формой для сбора контактов потенциальных клиентов.",
            "price": 1500,
            "deliveryTime": "2-3 дня",
            "icon": "📝",
            "imageUrl": "https://static.tildacdn.com/stor3033-6238-4636-b430-646562353430/63843752.png",
            "features": ["Форма обратной связи", "Призыв к действию", "Базовая аналитика"],
            "technologies": ["HTML5", "CSS3", "JavaScript", "PHP"],
            "category": "Веб-разработка"
        },
        {
            "name": "Многостраничный сайт",
            "shortDescription": "Сайт с несколькими страницами и навигацией",
            "fullDescription": "Разработка многостраничного сайта с навигацией, несколькими разделами и базовой системой управления контентом.",
            "price": 2000,
            "deliveryTime": "3-4 дня",
            "icon": "🌐",
            "imageUrl": "https://static.tildacdn.com/stor3761-3665-4831-b530-353134323764/93401530.png",
            "features": ["Навигационное меню", "Несколько страниц", "Галерея изображений"],
            "technologies": ["HTML5", "CSS3", "JavaScript"],
            "category": "Веб-разработка"
        },
        {
            "name": "Сайт с CMS",
            "shortDescription": "Сайт с системой управления контентом",
            "fullDescription": "Создание сайта с простой системой управления контентом для самостоятельного редактирования информации.",
            "price": 2500,
            "deliveryTime": "4-5 дней",
            "icon": "⚙️",
            "imageUrl": "https://static.tildacdn.com/tild3135-3466-4630-b932-663164646565/20250719_0400_____si.png",
            "features": ["Система управления", "Редактор контента", "Загрузка изображений"],
            "technologies": ["WordPress", "PHP", "MySQL"],
            "category": "Веб-разработка"
        },
        {
            "name": "Портфолио сайт",
            "shortDescription": "Сайт-портфолио для демонстрации работ",
            "fullDescription": "Разработка портфолио сайта для демонстрации работ и услуг с галереей проектов и описаниями.",
            "price": 3000,
            "deliveryTime": "4-5 дней",
            "icon": "🎨",
            "imageUrl": "https://static.tildacdn.com/tild3361-6635-4230-a638-663630326661/20250719_0359____sim.png",
            "features": ["Галерея работ", "Описания проектов", "Контактная форма"],
            "technologies": ["HTML5", "CSS3", "JavaScript"],
            "category": "Веб-разработка"
        },
        {
            "name": "Блог сайт",
            "shortDescription": "Сайт для ведения блога и публикаций",
            "fullDescription": "Создание блог-сайта с возможностью публикации статей, комментариев и подписки на обновления.",
            "price": 3500,
            "deliveryTime": "5-6 дней",
            "icon": "📰",
            "imageUrl": "https://static.tildacdn.com/stor6137-6261-4164-a461-643232623932/21775521.png",
            "features": ["Система публикаций", "Комментарии", "Поиск по блогу"],
            "technologies": ["WordPress", "PHP", "MySQL"],
            "category": "Веб-разработка"
        },
        {
            "name": "Каталог товаров",
            "shortDescription": "Сайт-каталог с товарами без покупки",
            "fullDescription": "Разработка каталога товаров с фильтрацией, поиском и детальными страницами продуктов без функций покупки.",
            "price": 4000,
            "deliveryTime": "6-7 дней",
            "icon": "📋",
            "imageUrl": "https://static.tildacdn.com/stor3132-6635-4365-a336-343664343038/15311280.png",
            "features": ["Каталог товаров", "Система фильтров", "Поиск", "Детальные страницы"],
            "technologies": ["PHP", "MySQL", "JavaScript"],
            "category": "Веб-разработка"
        },
        {
            "name": "Форум сайт",
            "shortDescription": "Простой форум для обсуждений",
            "fullDescription": "Создание форума с регистрацией пользователей, созданием тем и системой комментариев.",
            "price": 4500,
            "deliveryTime": "7-8 дней",
            "icon": "💬",
            "imageUrl": "https://static.tildacdn.com/stor6339-3837-4265-a639-316436316466/96992312.png",
            "features": ["Регистрация пользователей", "Создание тем", "Система комментариев"],
            "technologies": ["PHP", "MySQL", "JavaScript"],
            "category": "Веб-разработка"
        },
        {
            "name": "Новостной сайт",
            "shortDescription": "Сайт для публикации новостей",
            "fullDescription": "Разработка новостного сайта с категориями новостей, поиском и админ-панелью для управления.",
            "price": 5000,
            "deliveryTime": "7-8 дней",
            "icon": "📺",
            "imageUrl": "https://static.tildacdn.com/stor3938-6561-4131-a634-333063303364/92873101.png",
            "features": ["Категории новостей", "Админ-панель", "Поиск новостей"],
            "technologies": ["WordPress", "PHP", "MySQL"],
            "category": "Веб-разработка"
        },
        {
            "name": "Интеграция с API",
            "shortDescription": "Подключение внешних сервисов через API",
            "fullDescription": "Интеграция сайта с внешними API сервисами для получения данных или отправки информации.",
            "price": 5500,
            "deliveryTime": "3-4 дня",
            "icon": "🔗",
            "imageUrl": "https://static.tildacdn.com/stor3136-3864-4664-b930-353330343964/95301302.png",
            "features": ["API интеграция", "Обработка данных", "Синхронизация"],
            "technologies": ["PHP", "cURL", "JSON"],
            "category": "Интеграции"
        },
        {
            "name": "Мобильная адаптация",
            "shortDescription": "Адаптация сайта под мобильные устройства",
            "fullDescription": "Адаптация существующего сайта для корректного отображения на мобильных устройствах и планшетах.",
            "price": 6000,
            "deliveryTime": "4-5 дней",
            "icon": "📱",
            "imageUrl": "https://static.tildacdn.com/stor3263-3936-4532-a139-356366386335/74316926.png",
            "features": ["Мобильная версия", "Адаптивный дизайн", "Оптимизация скорости"],
            "technologies": ["CSS3", "JavaScript", "Bootstrap"],
            "category": "Веб-разработка"
        },
        {
            "name": "SEO оптимизация",
            "shortDescription": "Оптимизация сайта для поисковых систем",
            "fullDescription": "Комплексная SEO оптимизация сайта для улучшения позиций в поисковых системах.",
            "price": 6500,
            "deliveryTime": "5-6 дней",
            "icon": "📈",
            "imageUrl": "https://static.tildacdn.com/stor6264-3263-4539-b065-363233393231/13045211.png",
            "features": ["Мета-теги", "Карта сайта", "Оптимизация контента"],
            "technologies": ["HTML5", "Google Analytics", "Яндекс.Метрика"],
            "category": "Маркетинг"
        },
        {
            "name": "Интернет-магазин базовый",
            "shortDescription": "Простой интернет-магазин с корзиной",
            "fullDescription": "Создание базового интернет-магазина с каталогом, корзиной и простой системой заказов.",
            "price": 7000,
            "deliveryTime": "8-10 дней",
            "icon": "🛒",
            "imageUrl": "https://static.tildacdn.com/stor3162-3532-4733-b836-343063366234/89969513.png",
            "features": ["Каталог товаров", "Корзина", "Оформление заказов"],
            "technologies": ["PHP", "MySQL", "JavaScript"],
            "category": "E-commerce"
        },
        {
            "name": "Система регистрации",
            "shortDescription": "Система регистрации и авторизации пользователей",
            "fullDescription": "Разработка системы регистрации пользователей с личным кабинетом и управлением профилем.",
            "price": 7500,
            "deliveryTime": "5-6 дней",
            "icon": "👤",
            "imageUrl": "https://static.tildacdn.com/stor6232-3335-4430-a235-386135346339/87774497.png",
            "features": ["Регистрация", "Авторизация", "Личный кабинет"],
            "technologies": ["PHP", "MySQL", "Sessions"],
            "category": "Веб-разработка"
        },
        {
            "name": "Чат-бот для сайта",
            "shortDescription": "Простой чат-бот для сайта",
            "fullDescription": "Создание чат-бота для автоматических ответов на вопросы посетителей сайта.",
            "price": 8000,
            "deliveryTime": "4-5 дней",
            "icon": "🤖",
            "imageUrl": "https://static.tildacdn.com/stor6161-3734-4431-b063-616332663630/22565964.png",
            "features": ["Автоответы", "Интеграция с сайтом", "Настройка диалогов"],
            "technologies": ["JavaScript", "PHP", "MySQL"],
            "category": "Автоматизация"
        },
        {
            "name": "Галерея изображений",
            "shortDescription": "Фотогалерея с загрузкой изображений",
            "fullDescription": "Создание галереи изображений с возможностью загрузки, сортировки и просмотра фотографий.",
            "price": 8500,
            "deliveryTime": "6-7 дней",
            "icon": "🖼️",
            "imageUrl": "https://static.tildacdn.com/stor3565-6266-4266-a561-363036353838/15171739.png",
            "features": ["Загрузка изображений", "Сортировка", "Просмотр в полном размере"],
            "technologies": ["PHP", "JavaScript", "CSS3"],
            "category": "Веб-разработка"
        },
        {
            "name": "Система бронирования",
            "shortDescription": "Простая система онлайн бронирования",
            "fullDescription": "Разработка системы онлайн бронирования услуг или времени с календарем и уведомлениями.",
            "price": 9000,
            "deliveryTime": "7-8 дней",
            "icon": "📅",
            "imageUrl": "https://static.tildacdn.com/stor6230-3333-4234-a430-396662643166/71760452.png",
            "features": ["Календарь", "Бронирование времени", "Email уведомления"],
            "technologies": ["PHP", "JavaScript", "MySQL"],
            "category": "Системы управления"
        },
        {
            "name": "Интеграция с соцсетями",
            "shortDescription": "Подключение к социальным сетям",
            "fullDescription": "Интеграция сайта с социальными сетями для авторизации и публикации контента.",
            "price": 9500,
            "deliveryTime": "5-6 дней",
            "icon": "📱",
            "imageUrl": "https://static.tildacdn.com/tild3266-6461-4133-a261-613436326561/20250719_0338_____si.png",
            "features": ["Социальная авторизация", "Публикация в соцсети", "Виджеты"],
            "technologies": ["JavaScript", "OAuth", "API"],
            "category": "Интеграции"
        },
        {
            "name": "Многоязычный сайт",
            "shortDescription": "Сайт с поддержкой нескольких языков",
            "fullDescription": "Создание многоязычного сайта с переключением языков и переводом контента.",
            "price": 10000,
            "deliveryTime": "8-9 дней",
            "icon": "🌍",
            "imageUrl": "https://static.tildacdn.com/tild3662-6532-4461-b132-396531343831/20250719_0350____sim.png",
            "features": ["Переключение языков", "Перевод контента", "SEO для языков"],
            "technologies": ["PHP", "MySQL", "JavaScript"],
            "category": "Локализация"
        },
     {
            "name": "Одностраничный React SPA",
            "shortDescription": "Быстрый промо‑SPA на React",
            "fullDescription": "Разработка современного одностраничного приложения на React с роутингом без перезагрузки и оптимизацией Core Web Vitals.",
            "price": 10500,
            "deliveryTime": "4‑6 дней",
            "icon": "⚛️",
            "imageUrl": "https://static.tildacdn.com/tild6639-6635-4431-a239-356132363062/20250719_0305____sim.png",
            "gallery": [
                "https://static.tildacdn.com/tild6639-6635-4431-a239-356132363062/20250719_0305____sim.png",
                "https://static.tildacdn.com/tild6266-6461-4133-a261-613436326561/20250719_0338_____si.png"
            ],
            "features": ["React Router", "Ленивая подгрузка", "Пререндер для SEO"],
            "technologies": ["React", "Vite", "TypeScript"],
            "category": "Веб‑разработка"
        },
        {
            "name": "UX/UI аудит сайта",
            "shortDescription": "Экспресс‑аудит удобства интерфейса",
            "fullDescription": "Проводим экспертную оценку интерфейса по методике Nielsen, готовим отчёт с приоритетами улучшений и UI‑гайд.",
            "price": 11000,
            "deliveryTime": "3‑4 дня",
            "icon": "🔍",
            "imageUrl": "https://static.tildacdn.com/stor3933-3836-4237-b137-326362326338/19324104.png",
            "gallery": [
                "https://static.tildacdn.com/stor3933-3836-4237-b137-326362326338/19324104.png",
                "https://static.tildacdn.com/stor3932-3630-4334-b239-363039323661/29594603.png"
            ],
            "features": ["Heuristic evaluation", "User‑flow карта", "UI kit рекомендации"],
            "technologies": ["Figma", "Hotjar", "Google Analytics"],
            "category": "Аналитика"
        },
        {
            "name": "Каталог с 3D‑просмотром",
            "shortDescription": "Каталог товаров c 3D‑viewer",
            "fullDescription": "Разработка каталога, где каждый товар демонстрируется в интерактивном 3D‑просмотре (GLTF/GLB).",
            "price": 11500,
            "deliveryTime": "5‑7 дней",
            "icon": "🧊",
            "imageUrl": "https://static.tildacdn.com/stor6335-6461-4530-b561-393339346238/85806164.png",
            "gallery": [
                "https://static.tildacdn.com/stor6335-6461-4530-b561-393339346238/85806164.png",
                "https://static.tildacdn.com/stor6664-3064-4461-b736-313933353939/17425531.png"
            ],
            "features": ["3D model embed", "Сенсорное управление", "Оптимизация текстур"],
            "technologies": ["Three.js", "GLTF", "JavaScript"],
            "category": "E‑commerce"
        },
        {
            "name": "Импорт в Shopify",
            "shortDescription": "Миграция каталога в Shopify",
            "fullDescription": "Подготавливаем CSV, импортируем товары, настраиваем категории и оптимизируем изображения для Shopify.",
            "price": 12000,
            "deliveryTime": "4‑5 дней",
            "icon": "🛍️",
            "imageUrl": "https://static.tildacdn.com/stor3964-3536-4864-a439-373565363735/89268780.png",
            "gallery": [
                "https://static.tildacdn.com/stor3964-3536-4864-a439-373565363735/89268780.png",
                "https://static.tildacdn.com/stor3333-3534-4639-a231-356631616234/82449965.png"
            ],
            "features": ["CSV импорт", "Image optimization", "Category mapping"],
            "technologies": ["Shopify API", "Python", "Liquid"],
            "category": "Интеграции"
        },
        {
            "name": "Маркетплейс MVP",
            "shortDescription": "Мини‑маркетплейс для теста гипотезы",
            "fullDescription": "Запуск ядра маркетплейса: кабинеты продавцов, модерация товаров и базовые заказы.",
            "price": 12500,
            "deliveryTime": "7‑9 дней",
            "icon": "🛒",
            "imageUrl": "https://static.tildacdn.com/tild6534-3132-4265-b966-356464666561/20250719_0307___simp.png",
            "gallery": [
                "https://static.tildacdn.com/tild6534-3132-4265-b966-356464666561/20250719_0307___simp.png",
                "https://static.tildacdn.com/tild3235-6565-4737-a339-376665613364/20250719_0340___CI_C.png"
            ],
            "features": ["Seller accounts", "Product moderation", "Order tracking"],
            "technologies": ["Django", "PostgreSQL", "Celery"],
            "category": "E‑commerce"
        },
        {
            "name": "PWA‑приложение",
            "shortDescription": "Прогрессивное веб‑приложение",
            "fullDescription": "Добавляем офлайн‑режим, push‑уведомления и установку на главный экран для вашего сайта.",
            "price": 13000,
            "deliveryTime": "5‑6 дней",
            "icon": "📲",
            "imageUrl": "https://static.tildacdn.com/tild3662-6532-4461-b132-396531343831/20250719_0308___simp.png",
            "gallery": [
                "https://static.tildacdn.com/tild3662-6532-4461-b132-396531343831/20250719_0308___simp.png",
                "https://static.tildacdn.com/tild6638-3536-4735-b232-306532333134/20250719_0325___simp.png"
            ],
            "features": ["Service Worker", "Push notifications", "Offline cache"],
            "technologies": ["Workbox", "TypeScript", "Vite"],
            "category": "Веб‑разработка"
        },
        {
            "name": "Интерактивная инфографика",
            "shortDescription": "Динамические графики для отчётов",
            "fullDescription": "Создаём интерактивные графики с фильтрами и анимацией для презентации данных.",
            "price": 13500,
            "deliveryTime": "5‑6 дней",
            "icon": "📊",
            "imageUrl": "https://static.tildacdn.com/tild3565-6133-4061-b934-326632663862/20250719_0309___a_si.png",
            "gallery": [
                "https://static.tildacdn.com/tild3565-6133-4061-b934-326632663862/20250719_0309___a_si.png",
                "https://static.tildacdn.com/stor3736-6430-4166-a335-393061393438/68875476.png"
            ],
            "features": ["Chart.js", "Фильтры", "Адаптивный дизайн"],
            "technologies": ["Chart.js", "Vue 3", "TypeScript"],
            "category": "Презентации"
        },
        {
            "name": "Голосовой ассистент",
            "shortDescription": "Ассистент на сайте для голосовых команд",
            "fullDescription": "Интегрируем распознавание речи и синтез ответов, повышая доступность интерфейса.",
            "price": 14000,
            "deliveryTime": "6‑7 дней",
            "icon": "🎙️",
            "imageUrl": "https://static.tildacdn.com/stor3238-6135-4362-b865-316433653263/49713888.png",
            "gallery": [
                "https://static.tildacdn.com/stor3238-6135-4362-b865-316433653263/49713888.png",
                "https://static.tildacdn.com/tild3336-6366-4234-b933-663462386636/20250719_0342_____si.png"
            ],
            "features": ["Speech Recognition", "Text‑to‑Speech", "Фолбэк‑чат"],
            "technologies": ["Web Speech API", "JavaScript", "Python FastAPI"],
            "category": "Доступность"
        },
        {
            "name": "Облачный медиасервер",
            "shortDescription": "Стриминговый сервер под ключ",
            "fullDescription": "Настраиваем медиасервер с HLS‑стримингом, адаптивным битрейтом и панелью управления.",
            "price": 14500,
            "deliveryTime": "7‑9 дней",
            "icon": "📡",
            "imageUrl": "https://static.tildacdn.com/stor3536-3962-4036-b139-613466646430/60390468.png",
            "gallery": [
                "https://static.tildacdn.com/stor3536-3962-4036-b139-613466646430/60390468.png",
                "https://static.tildacdn.com/tild3166-6263-4134-b730-306261663636/20250719_0341____API.png"
            ],
            "features": ["HLS streaming", "Adaptive bitrate", "Admin dashboard"],
            "technologies": ["Nginx RTMP", "FFmpeg", "React"],
            "category": "Медиа"
        },
        {
            "name": "Микросервисный MVP",
            "shortDescription": "Базовая микросервисная архитектура",
            "fullDescription": "Проектируем и разворачиваем набор микросервисов в Docker с REST API и документацией Swagger.",
            "price": 16000,
            "deliveryTime": "8‑10 дней",
            "icon": "🔗",
            "imageUrl": "https://static.tildacdn.com/tild3436-3366-4061-b335-613663623466/20250719_0310__Agile.png",
            "gallery": [
                "https://static.tildacdn.com/tild3436-3366-4061-b335-613663623466/20250719_0310__Agile.png",
                "https://static.tildacdn.com/stor3963-3230-4236-b761-333532303962/28297582.png"
            ],
            "features": ["Docker Compose", "REST API", "Swagger Docs"],
            "technologies": ["Python FastAPI", "Docker", "PostgreSQL"],
            "category": "Архитектура"
        },
        {
            "name": "CI/CD автоматизация",
            "shortDescription": "Пайплайн деплоймента без рук",
            "fullDescription": "Настраиваем GitHub Actions: тесты, сборка, деплой и откат к стабильной версии.",
            "price": 17000,
            "deliveryTime": "4‑5 дней",
            "icon": "🚚",
            "imageUrl": "https://static.tildacdn.com/tild3866-3439-4663-b063-323934373139/20250719_0312____sim.png",
            "gallery": [
                "https://static.tildacdn.com/tild3866-3439-4663-b063-323934373139/20250719_0312____sim.png",
                "https://static.tildacdn.com/tild3938-6239-4431-b265-353734356136/20250719_0343____sim.png"
            ],
            "features": ["GitHub Actions", "Auto deploy", "Rollback"],
            "technologies": ["YAML", "Docker", "Kubernetes"],
            "category": "DevOps"
        },
        {
            "name": "Чат‑сервер высокой нагрузки",
            "shortDescription": "Realtime чат 50k RPS",
            "fullDescription": "Разворачиваем WebSocket‑сервер с горизонтальным масштабированием и хранением истории сообщений.",
            "price": 18000,
            "deliveryTime": "9‑12 дней",
            "icon": "💬",
            "imageUrl": "https://static.tildacdn.com/stor3134-6666-4431-b566-616130393262/12721519.png",
            "gallery": [
                "https://static.tildacdn.com/stor3134-6666-4431-b566-616130393262/12721519.png",
                "https://static.tildacdn.com/stor3662-6466-4930-b166-636539616536/37109528.png"
            ],
            "features": ["WebSocket", "Rate limiting", "Message history"],
            "technologies": ["Go", "Redis", "NATS"],
            "category": "Коммуникации"
        },
        {
            "name": "Дашборд аналитики данных",
            "shortDescription": "Realtime BI дашборд",
            "fullDescription": "Создаём дашборд с живыми метриками, экспортом CSV и разграничением прав доступа.",
            "price": 19000,
            "deliveryTime": "8‑10 дней",
            "icon": "📈",
            "imageUrl": "https://static.tildacdn.com/tild6363-3466-4637-a364-386135633636/20250719_0313_____si.png",
            "gallery": [
                "https://static.tildacdn.com/tild6363-3466-4637-a364-386135633636/20250719_0313_____si.png",
                "https://static.tildacdn.com/stor6661-3765-4430-a362-363838643734/97635607.png"
            ],
            "features": ["Live charts", "Export CSV", "RBAC"],
            "technologies": ["Vue 3", "D3.js", "ClickHouse"],
            "category": "Аналитика"
        },
        {
            "name": "WebView‑мобильное приложение",
            "shortDescription": "Нативные сборки iOS/Android",
            "fullDescription": "Упаковываем ваш сайт в нативное приложение с push‑уведомлениями и публикацией в сторах.",
            "price": 20000,
            "deliveryTime": "10‑12 дней",
            "icon": "📱",
            "imageUrl": "https://static.tildacdn.com/stor3033-6262-4237-a666-373731353230/30102704.png",
            "gallery": [
                "https://static.tildacdn.com/stor3033-6262-4237-a666-373731353230/30102704.png",
                "https://static.tildacdn.com/tild3133-3064-4138-b830-383037646165/20250719_0344____sim.png"
            ],
            "features": ["iOS build", "Android build", "Push service"],
            "technologies": ["Flutter", "Dart", "Firebase"],
            "category": "Мобильная разработка"
        },
        {
            "name": "Headless e‑commerce",
            "shortDescription": "Продвинутый интернет‑магазин",
            "fullDescription": "Next.js фронтенд + Strapi бэкенд, Stripe платежи и поиск Algolia — готово к росту трафика.",
            "price": 25000,
            "deliveryTime": "14‑18 дней",
            "icon": "🛍️",
            "imageUrl": "https://static.tildacdn.com/tild3335-3831-4330-a362-373332626237/20250719_0314____sim.png",
            "gallery": [
                "https://static.tildacdn.com/tild3335-3831-4330-a362-373332626237/20250719_0314____sim.png",
                "https://static.tildacdn.com/tild3264-6438-4038-b961-323536303039/20250719_0345____sim.png"
            ],
            "features": ["Next.js", "Stripe", "Algolia search"],
            "technologies": ["Next.js", "Strapi", "PostgreSQL"],
            "category": "E‑commerce"
        },
        {
            "name": "ML рекомендательная система",
            "shortDescription": "Персональные рекомендации",
            "fullDescription": "Настраиваем коллаборативную фильтрацию, REST API выдачи и периодическое переобучение.",
            "price": 30000,
            "deliveryTime": "20‑25 дней",
            "icon": "🤖",
            "imageUrl": "https://static.tildacdn.com/stor6535-3762-4630-b263-333362663539/16548988.png",
            "gallery": [
                "https://static.tildacdn.com/stor6535-3762-4630-b263-333362663539/16548988.png",
                "https://static.tildacdn.com/stor3464-3734-4937-b464-666536373238/37218240.png"
            ],
            "features": ["Collaborative filtering", "API", "Retraining script"],
            "technologies": ["Python", "TensorFlow", "Docker"],
            "category": "Machine Learning"
        },
        {
            "name": "Big Data платформа analytics",
            "shortDescription": "Аналитика на терабайтах данных",
            "fullDescription": "Разворачиваем кластер Spark, строим ETL‑поток и готовим дашборды в Superset.",
            "price": 35000,
            "deliveryTime": "25‑30 дней",
            "icon": "🗄️",
            "imageUrl": "https://static.tildacdn.com/stor6335-3837-4732-a332-623833633566/23030493.png",
            "gallery": [
                "https://static.tildacdn.com/stor6335-3837-4732-a332-623833633566/23030493.png",
                "https://static.tildacdn.com/tild3732-3133-4263-b436-663034343933/20250719_0348____sim.png"
            ],
            "features": ["Spark cluster", "ETL pipeline", "Superset"],
            "technologies": ["Apache Spark", "Airflow", "Parquet"],
            "category": "Big Data"
        },
        {
            "name": "Корпоративный портал с SSO",
            "shortDescription": "Интранет с единой авторизацией",
            "fullDescription": "Разрабатываем портал с LDAP/Keycloak‑SSO, модулем документов и иерархией ролей.",
            "price": 40000,
            "deliveryTime": "25‑30 дней",
            "icon": "🏢",
            "imageUrl": "https://static.tildacdn.com/stor3164-3936-4631-b862-663937626333/45295033.png",
            "gallery": [
                "https://static.tildacdn.com/stor3164-3936-4631-b862-663937626333/45295033.png",
                "https://static.tildacdn.com/stor3930-3365-4564-b035-376661306461/23368363.png"
            ],
            "features": ["Keycloak SSO", "Документооборот", "Ролевые модели"],
            "technologies": ["Java", "Spring Boot", "Keycloak"],
            "category": "Корпоративные системы"
        },
        {
            "name": "AR‑каталог продукции",
            "shortDescription": "Каталог в дополненной реальности",
            "fullDescription": "Модели USDZ/GLB, markerless AR, аналитика взаимодействий — товар оживает у клиента дома.",
            "price": 45000,
            "deliveryTime": "30‑35 дней",
            "icon": "🕶️",
            "imageUrl": "https://static.tildacdn.com/stor6633-3531-4366-a361-613433323064/32377880.png",
            "gallery": [
                "https://static.tildacdn.com/stor6633-3531-4366-a361-613433323064/32377880.png",
                "https://static.tildacdn.com/tild3264-3830-4235-a534-623533333137/20250719_0349__CI_CD.png"
            ],
            "features": ["USDZ/GLB", "Markerless AR", "Usage analytics"],
            "technologies": ["ARKit", "Three.js", "Swift"],
            "category": "AR/VR"
        },
        {
            "name": "Цифровая трансформация под ключ",
            "shortDescription": "Комплексная модернизация процессов",
            "fullDescription": "Аудит процессов, дорожная карта и внедрение ИТ‑решений для роста эффективности бизнеса.",
            "price": 50000,
            "deliveryTime": "40‑45 дней",
            "icon": "🌐",
            "imageUrl": "https://static.tildacdn.com/tild3838-6631-4331-b661-626366373033/20250719_0324____sim.png",
            "gallery": [
                "https://static.tildacdn.com/tild3838-6631-4331-b661-626366373033/20250719_0324____sim.png",
                "https://static.tildacdn.com/stor3234-6662-4531-b963-343234333533/89066987.png"
            ],
            "features": ["Process audit", "Roadmap", "Implementation"],
            "technologies": ["BPMN", "Python", "Kubernetes"],
            "category": "Консалтинг"
        }
]


async def initialize_products():
    """Initialize products in database if they don't exist"""
    try:
        # Check if products already exist
        existing_count = await db.products.count_documents({})
        if existing_count > 0:
            print(f"Products already exist in database: {existing_count}")
            return

        # Insert products with UUIDs
        products_with_ids = []
        for product_data in PRODUCTS_DATA:
            product = Product(**product_data)
            products_with_ids.append(product.dict())

        await db.products.insert_many(products_with_ids)
        print(f"Inserted {len(products_with_ids)} products into database")
    except Exception as e:
        print(f"Error initializing products: {e}")


async def is_webhook_verified() -> bool:
    """Проверяет, проходила ли точка вебхука первоначальную проверку."""

    record = await webhook_state_collection.find_one({"_id": WEBHOOK_VERIFICATION_STATE_ID})
    return bool(record and record.get("verified"))


async def mark_webhook_verified() -> None:
    """Помечает эндпоинт как успешно проверенный и сохраняет время проверки."""

    await webhook_state_collection.update_one(
        {"_id": WEBHOOK_VERIFICATION_STATE_ID},
        {"$set": {"verified": True, "verified_at": datetime.utcnow()}},
        upsert=True,
    )

@api_router.get("/products", response_model=List[Product])
async def get_products():
    """Get all products"""
    try:
        products = await db.products.find().to_list(1000)
        return [Product(**product) for product in products]
    except Exception as e:
        print(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail="Error fetching products")

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Get product by ID"""
    try:
        product = await db.products.find_one({"id": product_id})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return Product(**product)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching product: {e}")
        raise HTTPException(status_code=500, detail="Error fetching product")


@api_router.post("/cart/save")
async def save_cart(cart_data: dict):
    """Save cart to database"""
    try:
        session_id = cart_data.get("session_id", str(uuid.uuid4()))
        items = cart_data.get("items", [])

        cart = Cart(
            session_id=session_id,
            items=[CartItem(**item) for item in items]
        )

        # Update or insert cart
        await db.carts.replace_one(
            {"session_id": session_id},
            cart.model_dump(),
            upsert=True
        )

        return {"status": "success", "session_id": session_id}
    except Exception as e:
        print(f"Error saving cart: {e}")
        raise HTTPException(status_code=500, detail="Error saving cart")

@api_router.get("/cart/{session_id}")
async def get_cart(session_id: str):
    """Get cart by session ID"""
    try:
        cart = await db.carts.find_one({"session_id": session_id})
        if not cart:
            return {"items": []}
        return Cart(**cart)
    except Exception as e:
        print(f"Error fetching cart: {e}")
        raise HTTPException(status_code=500, detail="Error fetching cart")


@api_router.get("/qr-code/{bank}/{amount}")
async def get_qr_code_endpoint(bank: str, amount: int):
    """Get QR code URL for specific bank and amount"""
    try:
        qr_url = get_qr_code(bank, amount)
        if not qr_url:
            raise HTTPException(status_code=404, detail="QR code not found for this bank and amount")
        return {"qr_url": qr_url, "bank": bank, "amount": amount}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting QR code: {e}")
        raise HTTPException(status_code=500, detail="Error getting QR code")


@api_router.post("/webhook/transactions", response_model=WebhookProcessResult)
async def receive_transaction_webhook(request: Request):
    """Обрабатывает входящие уведомления от платёжного провайдера."""

    if not WEBHOOK_REDIRECT_URL:
        raise HTTPException(status_code=500, detail="Webhook redirect URL is not configured")

    already_verified = await is_webhook_verified()

    raw_body = await request.body()
    payload: Any = {}
    raw_payload = ""

    if not raw_body:
        logger.info(
            "Webhook verification ping with empty body. Redirecting to %s",
            WEBHOOK_REDIRECT_URL,
        )
        await mark_webhook_verified()
        return RedirectResponse(url=WEBHOOK_REDIRECT_URL, status_code=307)

    try:
        raw_payload = raw_body.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        payload = json.loads(raw_payload)
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    payload_is_empty_json = (
        (isinstance(payload, dict) and not payload)
        or (isinstance(payload, list) and not payload)
        or raw_payload.strip() == "{}"
    )

    if payload_is_empty_json:
        logger.info(
            "Webhook verification ping with empty JSON payload. Redirecting to %s",
            WEBHOOK_REDIRECT_URL,
        )
        await mark_webhook_verified()
        return RedirectResponse(url=WEBHOOK_REDIRECT_URL, status_code=307)

    if not already_verified:
        await mark_webhook_verified()
        logger.info("Webhook verification request received. Redirecting to %s", WEBHOOK_REDIRECT_URL)
        return RedirectResponse(url=WEBHOOK_REDIRECT_URL, status_code=307)

    if not payload:
        raise HTTPException(status_code=400, detail="Webhook payload is empty")

    event_data = WebhookPayload.model_validate(payload)
    saved_event_id = event_data.id or str(uuid.uuid4())

    record = {
        "_id": saved_event_id,
        "event_type": event_data.event_type,
        "payload": payload,
        "raw_payload": raw_payload,
        "headers": {key: value for key, value in request.headers.items()},
        "received_at": datetime.utcnow(),
    }

    try:
        await webhook_events_collection.update_one(
            {"_id": saved_event_id},
            {"$set": record},
            upsert=True,
        )
    except Exception as error:
        logger.exception("Failed to persist webhook payload: %s", error)
        raise HTTPException(status_code=500, detail="Failed to persist webhook data")

    logger.info("Webhook event %s stored successfully", saved_event_id)
    return WebhookProcessResult(saved_event_id=saved_event_id)



@api_router.get("/webhook/transactions/status", response_model=WebhookVerificationStatus)
async def get_webhook_verification_status() -> WebhookVerificationStatus:
    """Возвращает текущее состояние прохождения проверки вебхука."""

    record = await webhook_state_collection.find_one({"_id": WEBHOOK_VERIFICATION_STATE_ID})
    verified = bool(record and record.get("verified"))
    verified_at = record.get("verified_at") if record else None
    return WebhookVerificationStatus(verified=verified, verified_at=verified_at)


@api_router.get("/banks")
async def get_banks():
    """Get available banks"""
    return {"banks": BANKS}

# Root endpoint
@api_router.get("/")
async def root():
    return {"message": "DevServices API is running", "products_count": len(PRODUCTS_DATA)}

# Include the router in the main app
app.include_router(api_router)



# =============================================================================
# СТАТИЧЕСКИЕ ФАЙЛЫ И SPA ROUTING
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

print(f"Looking for static files in: {STATIC_DIR}")
print(f"Static directory exists: {STATIC_DIR.exists()}")
if STATIC_DIR.exists():
    print(f"Contents: {list(STATIC_DIR.iterdir())}")

if STATIC_DIR.exists():
    react_static_dir = STATIC_DIR / "static"
    if react_static_dir.exists():
        print(f"Found React static files in: {react_static_dir}")
        app.mount("/static", StaticFiles(directory=react_static_dir), name="static")
    else:
        print(f"Warning: React static directory not found at {react_static_dir}")


    @app.get("/favicon.ico")
    async def favicon():
        favicon_path = STATIC_DIR / "favicon.ico"
        if favicon_path.exists():
            return FileResponse(favicon_path)
        raise HTTPException(status_code=404, detail="Favicon not found")


    @app.get("/manifest.json")
    async def manifest():
        manifest_path = STATIC_DIR / "manifest.json"
        if manifest_path.exists():
            return FileResponse(manifest_path)
        raise HTTPException(status_code=404, detail="Manifest not found")


    @app.get("/robots.txt")
    async def robots():
        robots_path = STATIC_DIR / "robots.txt"
        if robots_path.exists():
            return FileResponse(robots_path)
        return FileResponse(STATIC_DIR / "index.html")


    @app.get("/{path:path}")
    async def serve_react_app(path: str):
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")

        file_path = STATIC_DIR / path
        if file_path.is_file():
            return FileResponse(file_path)

        index_path = STATIC_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)

        raise HTTPException(status_code=404, detail="Application not found")

else:
    print(f"Warning: Static directory not found at {STATIC_DIR}")
    @app.get("/{path:path}")
    async def no_static_fallback(path: str):
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        return {"error": "Static files not found. Please build the frontend first."}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await initialize_products()


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
