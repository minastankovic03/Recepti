import datetime
from flask import Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:pas123@db/app'

db = SQLAlchemy(app)
cors = CORS(app)

app.app_context().push()

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
if not database_exists(engine.url):
    create_database(engine.url)

#TABELE

class Recepti(db.Model):
    __tablename__ = 'Recepti'

    id = db.Column(db.Integer, primary_key=True)
    naziv = db.Column(db.String(50), nullable=False)
    opis = db.Column(db.String(255), nullable=False)
    istorija = db.Column(db.Text)
    uputstvo = db.Column(db.Text)
    vreme_pripreme = db.Column(db.Integer)
    tezina = db.Column(db.String(10))
    datum = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    slika = db.Column(db.String(255))

    sastojci = db.relationship("Sastojci", back_populates="recept", cascade="all, delete-orphan")
    ocene = db.relationship("Ocene", back_populates="recept", cascade="all, delete-orphan")

    def ispis(self):
        return {
            "id": self.id,
            "naziv": self.naziv,
            "opis": self.opis,
            "istorija": self.istorija,
            "datum": self.datum.isoformat(),
            "sastojci": [s.ispis() for s in self.sastojci],
            "tezina": self.tezina,
            "vreme_pripreme": self.vreme_pripreme,
            "uputstvo": self.uputstvo,
            "slika": self.slika,
            "ocene": [o.ispis() for o in self.ocene]
        }

class Sastojci(db.Model):
    __tablename__ = 'Sastojci'

    id = db.Column(db.Integer, primary_key=True)
    ime = db.Column(db.String(30), nullable=False)
    kolicina = db.Column(db.String(50))
    recept_id = db.Column(db.Integer, db.ForeignKey("Recepti.id"), nullable=False)

    recept = db.relationship("Recepti", back_populates="sastojci")

    def ispis(self):
        return {
            "id": self.id,
            "ime": self.ime,
            "kolicina": self.kolicina
        }

class Ocene(db.Model):
    __tablename__ = 'Ocene'

    id = db.Column(db.Integer, primary_key=True)
    ocena = db.Column(db.Integer, nullable=False)
    recept_id = db.Column(db.Integer, db.ForeignKey("Recepti.id"), nullable=False)

    recept = db.relationship("Recepti", back_populates="ocene")

    def ispis(self):
        return {
            "id": self.id,
            "ocena": self.ocena
        }

class ListaKupovine(db.Model):
    __tablename__ = "Lista_za_kupovinu"

    id = db.Column(db.Integer, primary_key=True)
    ime = db.Column(db.String(50), nullable=False)
    kolicina = db.Column(db.String(30))

    def __init__(self, ime, kolicina):
        self.ime = ime
        self.kolicina = kolicina


with app.app_context():
    db.create_all()

#RUTE

@app.route("/", methods=["GET"])
def poruka():
    return {"poruka": "Dobrodošli u aplikaciju za recepte!"}

@app.route("/recepti", methods=["GET"])
def get_recepti():
    recepti = Recepti.query.all()
    return [r.ispis() for r in recepti]

@app.route("/recepti", methods=["POST"])
def kreiraj_recept():
    podaci = request.json
    recept = Recepti(
        naziv=podaci["naziv"],
        opis=podaci["opis"],
        istorija=podaci.get("istorija"),
        uputstvo=podaci.get("uputstvo"),
        tezina=podaci.get("tezina"),
        vreme_pripreme=podaci.get("vreme_pripreme"),
        slika=podaci.get("slika")
    )
    for s in podaci.get("sastojci", []):
        recept.sastojci.append(Sastojci(ime=s["ime"], kolicina=s["kolicina"]))
    db.session.add(recept)
    db.session.commit()
    return recept.ispis(), 201

@app.route("/recepti/<int:id>", methods=["PUT"])
def azuriraj_recept(id):
    recept = Recepti.query.get(id)
    if not recept:
        return {"poruka": "Recept nije pronađen"}, 404

    data = request.json
    recept.naziv = data.get("naziv", recept.naziv)
    recept.opis = data.get("opis", recept.opis)
    recept.istorija = data.get("istorija", recept.istorija)
    recept.uputstvo = data.get("uputstvo", recept.uputstvo)
    recept.tezina = data.get("tezina", recept.tezina)
    recept.vreme_pripreme = data.get("vreme_pripreme", recept.vreme_pripreme)
    recept.slika = data.get("slika", recept.slika)

    db.session.commit()
    return recept.ispis()

@app.route("/recepti/<int:id>", methods=["DELETE"])
def obrisi_recept(id):
    recept = Recepti.query.get(id)
    if not recept:
        return {"poruka": "Recept nije pronađen"}, 404
    if recept.naziv in ["Bakin ajvar", "Pinđur","Kisele paprike","Proja", "Pileća čorba","Bajadere","Rolat sa orasima","Torta od palačinki"]:
        return {"poruka": "Ovaj recept je deo početnih recepata i ne može se obrisati."}, 403
    db.session.delete(recept)
    db.session.commit()
    return {"poruka": f"Recept je obrisan."}

@app.route("/pretraga", methods=["GET"])
def pretraga_recepta():
    naziv = request.args.get("naziv")
    sastojak = request.args.get("sastojak")
    upit = Recepti.query
    if naziv:
        upit = upit.filter(Recepti.naziv.ilike(f"%{naziv}%"))
    if sastojak:
        upit = upit.join(Recepti.sastojci).filter(Sastojci.ime.ilike(f"%{sastojak}%"))

    return [r.ispis() for r in upit.all()]

@app.route("/recepti/<int:id>/ocena", methods=["POST"])
def dodaj_ocenu(id):
    recept = Recepti.query.get(id)
    if not recept:
        return {"poruka": "Recept nije pronađen"}, 404
    ocena = request.json["ocena"]
    nova = Ocene(ocena=ocena, recept=recept)
    db.session.add(nova)
    db.session.commit()
    return {"poruka": "Ocena dodata", "ocena": nova.ispis()}

@app.route("/kupovina", methods=["POST"])
def dodaj_u_kupovinu():
    data = request.json
    if not data.get("ime"):
        return {"error": "Ime artikla je obavezno"}, 400

    artikal = ListaKupovine(ime=data["ime"], kolicina=data.get("kolicina"))
    db.session.add(artikal)
    db.session.commit()

    return {
        "id": artikal.id,
        "ime": artikal.ime,
        "kolicina": artikal.kolicina
    }, 201

@app.route("/kupovina", methods=["GET"])
def get_lista_kupovine():
    artikli = ListaKupovine.query.all()
    return [
        {"id": a.id, "ime": a.ime, "kolicina": a.kolicina}
        for a in artikli
    ]

@app.route("/kupovina/<int:item_id>", methods=["DELETE"])
def obrisi_stavku_kupovine(item_id):
    artikal = ListaKupovine.query.get(item_id)
    if not artikal:
        return {"error": "Stavka nije pronađena"}, 404

    db.session.delete(artikal)
    db.session.commit()
    return {"message": f"Stavka {item_id} obrisana."}, 200

@app.route("/kupovina/<int:item_id>", methods=["PUT"])
def azuriraj_stavku_kupovine(item_id):
    artikal = ListaKupovine.query.get(item_id)
    if not artikal:
        return {"error": "Stavka nije pronađena"}, 404
    data = request.json
    artikal.ime = data.get("ime", artikal.ime)
    artikal.kolicina = data.get("kolicina", artikal.kolicina)

    db.session.commit()
    return {
        "id": artikal.id,
        "ime": artikal.ime,
        "kolicina": artikal.kolicina
    }

@app.route("/top-recepti", methods=["GET"])
def top_recepti():
    recepti = (
        db.session.query(Recepti, func.avg(Ocene.ocena).label("prosek"))
        .outerjoin(Ocene)
        .group_by(Recepti.id)
        .order_by(func.avg(Ocene.ocena).desc())
        .limit(10)
        .all()
    )
    rezultat = []
    for r, prosek in recepti:
        podaci = r.ispis()
        podaci["prosek_ocena"] = round(prosek, 2) if prosek else None
        rezultat.append(podaci)

    return rezultat

#INICIJALNI RECEPTI
with app.app_context():
    if not Recepti.query.first():  
        r1 = Recepti(
            naziv="Bakin ajvar",
            opis="Najpoznatija srpska zimnica od paprike",
            istorija="Ajvar je specijalna vrsta zimnice, specijalitet balkanske kuhinje, napravljena od crvene paprike. Ajvar je poreklom s Balkana.Koristi se kao dodatak mnogim jelima, a najčešće kao hlebni namaz. Uz papriku se najčešće dodaje i plavi patlidžan. Ajvar se tradicionalno pravi na jesen, kada je puna sezona paprike, i koristi cele godine. Ajvar se pravi i od ljutih i od slatkih paprika.",
            uputstvo="Paprike ispeći, oljuštiti ih, očistiti od semenki i zatim dobro ocediti. Patlidžan takođe ispeći i oljuštiti. Samleti paprike i patlidžan. Smesu sipati u šerpu sa širokim dnom da se zagreje, a zatim dodati ulje (iz dva dela). Stalno mešati i tako pržiti oko 2h. Pred kraj dodati so i esenciju. Tegle zagrejati u rerni na 100°C. Ajvar sipati u zagrejane tegle (bez zatvaranja tegli) i ostaviti u rerni da prenoće. Sutradan zatvoriti tegle.",
            vreme_pripreme=480,
            tezina="Teško",
            slika="http://localhost:5000/static/slike/Ajvar.jpg"
        )
        r1.sastojci.append(Sastojci(ime="Paprike", kolicina="8-10 kg"))
        r1.sastojci.append(Sastojci(ime="Patlidžan", kolicina="2 kg"))
        r1.sastojci.append(Sastojci(ime="Ulje", kolicina="500 ml"))
        r1.sastojci.append(Sastojci(ime="So", kolicina="po ukusu"))
        r1.sastojci.append(Sastojci(ime="Esencija", kolicina="2 sk"))

        r2 = Recepti(
            naziv="Pinđur",
            opis="Blago ljuta srpska zimnica",
            istorija="Pinđur je vrsta začinjenoga namaza popularnoga u kuhinjama naroda jugoistočne Europe. Sličan je ajvaru, ali se razlikuje po tome što su mu glavni sastojci paprika i paradajz, a ne paprika i patlidžan. U poređenju s ajvarom, ukus pinđura je nešto blaži jer paradajz svojom svežom, blago kiselom aromom ublažava ukus pečene paprike, dok ga beli luk čini aromatičnijim. Po želji može biti i ljut. I tekstura im je različita, ajvar je nešto gušći od pinđura, pa iako se oba mogu namazati na hleb ili poslužiti kao prilozi, kao sastojci tokom kuvanja ajvar i pinđur imaju svaki svoju preporučenu upotrebu.",
            uputstvo="Paprike ispeći, oljuštiti, skinuti peteljke i semenke, a potom preko noći iscediti. Isto ponoviti i sa ljutim papričicama. Paradajz oprati, očistiti i iseći na manje kriške (ne ljuštiti). U veću šerpu sipati ulje, sirće i šećer, pa kada blago počne da vri dodati paradajz, kuvati oko 2h (ili dok voda od paradajza ne ispari). Paprike i ljute papričice iseći na što sitnije kockice. Peršun iskidati na listiće i iseckati. Beli luk očistiti i iseći na listiće. Kada se paradajz ukuvao prvo dodati papriku i ljute papričice. Nakon 30-45 min dodati peršun, a potom i beli luk. Na kraju posoliti. Krčkati još oko 30 min. Tegle zagrejati u rerni na 100°C. Pinđur sipati u zagrejane tegle (bez zatvaranja tegli) i ostaviti u rerni da prenoće. Sutradan zatvoriti tegle.",
            vreme_pripreme=480,
            tezina="Teško",
            slika="http://localhost:5000/static/slike/pinđur.jpg"
        )
        r2.sastojci.append(Sastojci(ime="Paprike", kolicina="3.5 kg"))
        r2.sastojci.append(Sastojci(ime="Paradajz", kolicina="2.3 kg"))
        r2.sastojci.append(Sastojci(ime="Beli luk", kolicina="2 glavice"))
        r2.sastojci.append(Sastojci(ime="Ljute papričice", kolicina="4 kom"))
        r2.sastojci.append(Sastojci(ime="Peršun", kolicina="2 veze"))
        r2.sastojci.append(Sastojci(ime="Šećer", kolicina="110 g"))
        r2.sastojci.append(Sastojci(ime="Sirće", kolicina="400 g"))
        r2.sastojci.append(Sastojci(ime="Ulje", kolicina="375 ml"))
        r2.sastojci.append(Sastojci(ime="So", kolicina="1.5 sk"))

        r3 = Recepti(
            naziv="Kisele paprike",
            opis="Ukusna zimska salata",
            istorija="",
            uputstvo="Paprike izdubiti i očistiti od semenki, peći u rerni na 200°C 10 min. Ređati u šerpu i zatvoriti na 24h. Promešati nekoliko puta. Poređati paprike u tegle. Pomešati so, šećer, vinobran, konzervans, esenciju, beli luk i peršun. Preliti preko paprika nakon što su poređane u teglu. Na kraju preliti sokom koji je pustila paprika i zatvoriti teglu.",
            vreme_pripreme=240,
            tezina="Srednje",
            slika="http://localhost:5000/static/slike/kisele-paprike.jpg"
        )
        r3.sastojci.append(Sastojci(ime="Paprike", kolicina="10 kg"))
        r3.sastojci.append(Sastojci(ime="Vinobran", kolicina="1 kesica"))
        r3.sastojci.append(Sastojci(ime="Konzervans", kolicina="1 kesica"))
        r3.sastojci.append(Sastojci(ime="Esencija", kolicina="1 šolja"))
        r3.sastojci.append(Sastojci(ime="Peršun", kolicina="2 veze"))
        r3.sastojci.append(Sastojci(ime="Šećer", kolicina="14 sk"))
        r3.sastojci.append(Sastojci(ime="Beli luk", kolicina="4 glavice"))
        r3.sastojci.append(Sastojci(ime="So", kolicina="8 sk"))

        r4 = Recepti(
            naziv="Proja",
            opis="Specijalitet od kukuruznog brašna",
            istorija="Proja, moruznica ili proha je kukuruzni hleb. Često se meša sa projanicom ili projarom. U jugoistočnoj Srbiji proja je poznata pod nazivom „moruznica” i deo je 'Gastronomije pirotskog kraja'. Proja je bitan deo srpske kuhinje gde služi kao predjelo.",
            uputstvo="Umutiti jaja, dodati so a zatim i kukuruzno brašno. Dodati obično brašno, pa jogurt/pavlaku/kiselo mleko. Dodati prašak za pecivo i ulje. Ostaviti malo da odstoji. Izliti u tepsiju i izmrviti sir odozgo. Peći 30 min na 180°C.",
            vreme_pripreme=60,
            tezina="Lako",
            slika="http://localhost:5000/static/slike/proja.jpg"
        )
        r4.sastojci.append(Sastojci(ime="Jaja", kolicina="4-5 kom"))
        r4.sastojci.append(Sastojci(ime="Jogurt/Pavlaka/Kiselo mleko", kolicina="1 čaša"))
        r4.sastojci.append(Sastojci(ime="Kukuruzno brašno", kolicina="2 šolje"))
        r4.sastojci.append(Sastojci(ime="Pšenično brašno", kolicina="1 šolja"))
        r4.sastojci.append(Sastojci(ime="Prašak za pecivo", kolicina="1 kesica"))
        r4.sastojci.append(Sastojci(ime="Ulje", kolicina="1.5 šolja"))
        r4.sastojci.append(Sastojci(ime="Sir", kolicina="1 kriška"))
        
        r5 = Recepti(
            naziv="Pileća čorba",
            opis="Jedna od omiljenih čorba u Srbiji",
            istorija="Čorba je vrsta supe karakteristična za Balkan ali pre svega za Tursku kao i zemlje kao što su Rusija, Kazahstan. Čorba potiče iz Turske i pravila se pre svega od škembića. Sve ostale kasnije varijante čorbe - dodavanje milerama, soka od limuna, druge vrste mesa, povrća i slično, su samo kasnije varijante. U Osmanskom carstvu je čak postojao esnaf čorbadžija. Kod janjičara čin pukovnika se zvao čorbadžija.",
            uputstvo="U loncu skuvati batake u posoljenoj vodi sa malo začina i bibera. U drugom loncu izdinstati luk, praziluk, pa dodati ostalo povrće iseckano na kockice. Ponovo dodati malo začina, bibera i brašna. Kada je meso kuvano očistiti ga od kostiju i kožice i iscepkati na komadiće. Procediti supu od mesa u lonac sa povrćem, dodati meso i pustiti da provri. Nakon toga kuvati jos 10-ak min. Po želji dodati umućeno jaje ili pavlaku.",
            vreme_pripreme=120,
            tezina="Srednje",
            slika="http://localhost:5000/static/slike/pileca-corba.jpg"
        )
        r5.sastojci.append(Sastojci(ime="Batak/Karabatak", kolicina="4 kom"))
        r5.sastojci.append(Sastojci(ime="Crni luk", kolicina="1 glavica"))
        r5.sastojci.append(Sastojci(ime="Praziluk", kolicina="1 kom"))
        r5.sastojci.append(Sastojci(ime="Šargarepa", kolicina="2 kom"))
        r5.sastojci.append(Sastojci(ime="Paškanat", kolicina="0.5 kom"))
        r5.sastojci.append(Sastojci(ime="Bela zelen", kolicina="0.5 kom"))
        r5.sastojci.append(Sastojci(ime="Celer", kolicina="0.5 kom"))
        r5.sastojci.append(Sastojci(ime="Ulje", kolicina="100 ml"))
        r5.sastojci.append(Sastojci(ime="So", kolicina="1 kk"))
        r5.sastojci.append(Sastojci(ime="Biber", kolicina="po želji"))
        r5.sastojci.append(Sastojci(ime="Začin/Vegeta", kolicina="po želji"))
        r5.sastojci.append(Sastojci(ime="Jaje", kolicina="po želji"))
        r5.sastojci.append(Sastojci(ime="Pavlaka", kolicina="po želji"))

        r6 = Recepti(
            naziv="Bajadere",
            opis="Brz i preukusan dezert",
            istorija="Bajadera (fr. bayadère — „plesačica u hramu”) je desert koji se koristi u Srbiji i regionu i često je prisutan na slavskoj trpezi. Bajadera je dobila na popularnosti zahvaljujući istoimenom proizvodu kompanije Kraš, koji je bio popularan na prostorima bivše Jugoslavije, a koji je zapravo industrijski stabilna varijanta ovog kolača u kojoj umesto oraha dominiraju lešnici. Kolač je izvorno mrsan, ali se može realizovati i kao posan ako se umesto putera upotrebi margarin.",
            uputstvo="Ušpinovati šećer sa vodom i dodati puter. Zatim u to umešati keks i orahe, kada se dobro sjedini izliti u pleh. Istopiti čokoladu i dodati kašiku ulja. Preliti smesu u plehu glazurom od čokolade. Kada se malo prohladi, ostaviti preko noći u frižideru da se stegne.",
            vreme_pripreme=80,
            tezina="Lako",
            slika="http://localhost:5000/static/slike/bajadere.jpg"
        )
        r6.sastojci.append(Sastojci(ime="Mleveni orasi", kolicina="300 g"))
        r6.sastojci.append(Sastojci(ime="Mleveni keks", kolicina="200 g"))
        r6.sastojci.append(Sastojci(ime="Puter", kolicina="150 g"))
        r6.sastojci.append(Sastojci(ime="Šećer", kolicina="400 g"))
        r6.sastojci.append(Sastojci(ime="Voda", kolicina="10 sk"))
        r6.sastojci.append(Sastojci(ime="Čokolada za kuvanje", kolicina="200 g"))
        r6.sastojci.append(Sastojci(ime="Ulje", kolicina="1 sk"))
        
        r7 = Recepti(
            naziv="Rolat sa orasima",
            opis="Starinski domaći kolač koji svi obožavaju",
            istorija="Strogo povreljivo! ;)",
            uputstvo="Umutiti belanca u sneg, dodati šećer, pa još umutiti. Dodati žumanca. Dodati prosejano brašno i lagano umutiti. Pleh obložiti papirom za pečenje. Smesu ravnomerno rasporediti špatulom u tankom sloju na plehu. Peći oko 30 min na 180-200°C. Za fil u posudi ugrejati šećer sa vodom, dodati malo soli i vanil šećer. Mešati dok se šećer dobro ne istopi, pa dodati puter i na kraju orahe. Mešati na laganoj vatri još par minuta. Kada se kora ispeče izvaditi je iz pleha i staviti na unapred pripremljenu podlogu od pak-papira koji je posut prah šećerom. Koru namazati džemom po želji, a zatim naneti i fil. Uviti kao rolat, umotati u papir i kuhinjsku krpu preko. Ostaviti da odstoji dok se prohladi, a potom staviti u frižider. Seći na kolutove i tako servirati.",
            vreme_pripreme=140,
            tezina="Teško",
            slika="http://localhost:5000/static/slike/rolat.jpg"
        )
        r7.sastojci.append(Sastojci(ime="Jaja", kolicina="6 kom"))
        r7.sastojci.append(Sastojci(ime="Šećer - patišpanj", kolicina="6 sk"))
        r7.sastojci.append(Sastojci(ime="Brašno", kolicina="5 sk"))
        r7.sastojci.append(Sastojci(ime="So", kolicina="1 prstohvat"))
        r7.sastojci.append(Sastojci(ime="Orasi", kolicina="300 g"))
        r7.sastojci.append(Sastojci(ime="Šećer - fil", kolicina="300 g"))
        r7.sastojci.append(Sastojci(ime="Vanil šećer", kolicina="1 kesica"))
        r7.sastojci.append(Sastojci(ime="Voda", kolicina="8 sk"))
        r7.sastojci.append(Sastojci(ime="Puter", kolicina="90 g"))
        r7.sastojci.append(Sastojci(ime="Džem - po želji", kolicina="5 sk"))

        r8 = Recepti(
            naziv="Torta od palačinki",
            opis="Omiljeni slatkiš sve dece",
            istorija="Veruje se da su prve palačinke nastale još u kamenom dobu, pre više od 30.000 godina. Analize su pokazale da su ljudi pravili palačinke od različitih žitarica koje su mlevene u brašno i mešane sa mlekom i jajima. Kroz vekove, palačinke su evoluirale zajedno sa ljudskom civilizacijom, prilagođavajući se lokalnim sastojcima i ukusima. U antičkoj Grčkoj i Rimu, palačinke su bile poznate kao tagenias i alita dolcia i često su se služile sa medom. U srednjem veku, palačinke su postale popularne širom Evrope, posebno tokom posta, kada su predstavljale način da se iskoriste jaja i mlečni proizvodi pre početka posta. Kasnije, osmišljene su razne verzije jela sa palačinkama, popust pohovanih palačinki i torte od palačinku.",
            uputstvo="Žumanaca umutiti sa šećerom. Dodati ulje, mleko, a potom i brašno. Dobro umutiti. Umutiti odvojeno belanaca u sneg, a zatim dodati u prethodnu smesu. Izlivati palačinke u tiganj i peći sa jedne strane. Izvaditi ovako pečenu palacinku pa tanjir, pa posuti šećerom i mlevenim orasima. Ređati palačinke jednu na drugu i filovati između. Istopiti 150g čokolade i dodati kašiku ulja. Preliti palačinke glazurom od čokolade. Kada se torta prohladi, staviti u frižider.",
            vreme_pripreme=120,
            tezina="Srednje",
            slika="http://localhost:5000/static/slike/palacinka-torta.jpg"
        )
        r8.sastojci.append(Sastojci(ime="Jaja", kolicina="5 kom"))
        r8.sastojci.append(Sastojci(ime="Šećer - smesa", kolicina="5 sk"))
        r8.sastojci.append(Sastojci(ime="Ulje - smesa", kolicina="5 sk"))
        r8.sastojci.append(Sastojci(ime="Brašno", kolicina="10 sk"))
        r8.sastojci.append(Sastojci(ime="Mleko", kolicina="0.5 l"))
        r8.sastojci.append(Sastojci(ime="Šećer - fil", kolicina="300 g"))
        r8.sastojci.append(Sastojci(ime="Mleveni orasi", kolicina="300 g"))
        r8.sastojci.append(Sastojci(ime="Ulje - glazura", kolicina="1 sk"))
        r8.sastojci.append(Sastojci(ime="Čokolada", kolicina="150 g"))
    

        db.session.add_all([r1, r2,r3,r4,r5,r6,r7,r8])
        db.session.commit()


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
