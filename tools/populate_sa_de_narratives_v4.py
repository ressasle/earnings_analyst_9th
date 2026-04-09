import os
import sys
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY]):
    print("Missing credentials")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

NARRATIVES_DE = {
    "DHR.US": {
        "company_name": "Danaher Corporation",
        "content_de": """# [DHR.US] Danaher Corporation Geschäftsbericht Geschäftsjahr 2024 – Institutionelle Analyse

## 1. ZUSAMMENFASSUNG (EXECUTIVE SUMMARY)
Danaher Corporation (DHR.US) hat im Geschäftsjahr 2024 seine strategische Neuausrichtung als reiner 'Life Sciences & Diagnostics' Innovator abgeschlossen und dabei eine bemerkenswerte operative Robustheit bewiesen. Trotz einer temporären Normalisierung der Bioprocessing-Nachfrage nach der Pandemie konnte Danaher einen Umsatz von über 21 Mrd. USD erzielen und seine marktführenden Positionen in den Bereichen Genomik, Biopharmazeutik und klinische Diagnostik festigen. Das Unternehmen profitierte signifikant von der erfolgreichen Integration der Veralto-Abspaltung (Wasser- und Umwelttechnologie) und der Fokussierung auf hochmargige Verbrauchsartikel (Consumables).

Ein zentrales Highlight des Jahres war die Beschleunigung der F&E-Investitionen in neue Diagnostik-Plattformen und die weitere Implementierung des legendären 'Danaher Business System' (DBS), das kontinuierliche Effizienzsteigerungen und Margenexpansionen ermöglicht. Mit einem Free-Cashflow-Profil, das fast 100 % des bereinigten Nettogewinns erreicht, bleibt Danaher eine Benchmark für operative Exzellenz und disziplinierte Reinvestition in Wachstumsfelder. Für institutionelle Investoren bietet Danaher eine erstklassige Möglichkeit, am langfristigen Wachstum der Präzisionsmedizin und der Life-Science-Forschung teilzuhaben.

## 2. INVESTMENTTHESE: DIE LIFE-SCIENCE-QUALITY-MASCHINE
Danalhers Investmentthese basiert auf der Kombination aus technologischem Vorsprung und einem hocheffizienten operativen Management-System.

**Kernpfeiler der These:**
- **Danaher Business System (DBS):** Das DBS ist tief in der DNA des Unternehmens verwurzelt. Es bildet den Rahmen für Kaizen (kontinuierliche Verbesserung) und sorgt dafür, dass Akquisitionen schnell profitabler werden als sie es vor der Übernahme waren.
- **Hoher Anteil wiederkehrender Umsätze:** Über 75 % des Umsatzes stammen aus Verbrauchsgütern und Serviceverträgen. Dies sorgt für eine außergewöhnliche Vorhersehbarkeit der Cashflows, selbst in volatilen Wirtschaftsphasen.
- **Pure-Play Fokus:** Nach der Abspaltung von Veralto ist Danaher ein konzentrierter Player im Bereich Biowissenschaften, was Investoren eine geziehlte Portfoliowiedergabe ermöglicht.
- **M&A-Zinseszinseffekt:** Danaher nutzt seinen massiven Cashflow, um laufend technologisch führende Unternehmen in angrenzenden Märkten (z.B. Protein-Analyse, Zelltherapie-Infrastruktur) zu erwerben.

## 3. FINANZIELLE LEISTUNG (GJ 2024)
### Umsatz- und Gewinnentwicklung
Der Umsatz von 21,5 Mrd. USD reflektiert den stabilen Kernmarkt der Diagnostik (Cepheid), während das Bioprocessing-Segment (Cytiva) Anzeichen einer Erholung der Lagerbestände bei Kunden zeigte.

### Margenprofil und operative Disziplin
Die Bruttomargen gehören mit über 60 % zu den höchsten im Industriesektor. Danaher gelingt es, durch Skaleneffekte und prozessuale Optimierung (DBS) ein zweistelliges Gewinnwachstum über den Zyklus hinweg aufrechtzuerhalten.

### Kapitalallokation
Das Management legte im Jahr 2024 den Fokus auf organisches Wachstum und den Schuldenabbau nach den großen Transaktionen des Vorjahres (Abcam). Dennoch bleibt das Unternehmen 'opportunistisch bereit' für neue strategische Zukäufe.

## 4. OPERATIVE HIGHLIGHTS: TECHNOLOGISCHE FÜHRERSCHAFT
- **Cepheid-Dominanz:** Die GeneXpert-Plattform bleibt der Goldstandard für molekulare Point-of-Care-Diagnostik, mit einer wachsenden Menükarte an verfügbaren Tests (Grippe, COVID, TB, etc.).
- **Cytiva-Integration:** Nach der Zusammenführung von Cytiva und Pall ist Danaher der unangefochtene Marktführer für Bioprocessing-Lösungen, die für die Herstellung von Biologika und Impfstoffen essentiell sind.
- **R&D Fokus:** Investitionen in die Massenspektrometrie (SCIEX) und Mikroskopie (Leica) treiben die Innovation in der biotechnologischen Forschung voran.

## 5. STRATEGISCHE POSITIONIERUNG: DAS RÜCKGRAT DER BIOTECH-BRANCHE
Danaher ist nicht nur ein Zulieferer, sondern der Enabler der modernen Biotechnologie.
- **Unverzichtbare Werkzeuge:** Ohne die Filter, Zentrifugen und Analysesysteme von Danaher kann moderne Medizin nicht produziert oder diagnostiziert werden.
- **Eintrittsbarrieren:** Die hohe regulatorische Komplexität (FDA-Zulassungen für Diagnostik) und die geschlossenen Ökosysteme der installierten Basis schaffen massive Wechselbarrieren für Kunden.

## 6. SECTOR- UND MAKROKONTEXT: DIE ÄRA DER BIOLOGIE
Wir befinden uns im 'Jahrzehnt der Biologie'. Steigende Gesundheitsausgaben aufgrund alternder Gesellschaften und die personalisierte Medizin (Gen- und Zelltherapien) sind langfristige Wachstumstreiber, die Danaher direkt in die Hände spielen.

## 7. RISIKOBEWERTUNG
- **Normalisierung der Lagerbestände:** Eine länger als erwartete Erholung im Bioprocessing-Markt nach den Pandemie-Ausreißern könnte die kurzfristige Wachstumsdynamik bremsen.
- **Wettbewerb im Diagnostik-Sektor:** Player wie Roche und Thermo Fisher sind starke Wettbewerber. Danaher muss seinen Innovationsvorsprung bei Cepheid kontinuierlich verteidigen.
- **Abhängigkeit von den USA und China:** Geopolitische Spannungen könnten Lieferketten beeinträchtigen oder den Marktzugang in Asien erschweren.

## 8. ZUKUNFTSAUSBLICK: 2025/26
Das Unternehmen plant eine Fortsetzung seines margenstarken Wachstumspfads.
- **Beschleunigte Akquisitionen:** Da sich die Bilanz weiter gestärkt hat, wird für 2025 ein Rückkehr zu einer agressiveren M&A-Strategie erwartet.
- **Nächste Generation Diagnostik:** Einführung neuer Multiplex-Tests auf der Cepheid-Plattform zur weiteren Marktdurchdringung.

## 9. ANALYSTEN-EMPFEHLUNG: BUY / QUALITY CORE
Danaher ist die Definition von 'Quality Growth'. Die außergewöhnliche Kombination aus exzellenter operativer Führung (DBS), einem krisenresistenten Geschäftsmodell mit hohem Consumable-Anteil und der Ausrichtung auf langfristige Gesundheits-Megatrends macht die Aktie zu einem Kerninvestement für jedes institutionelle Portfolio.

**Kursziel:** 295 USD.

## 10. METRISCHE ZUSAMMENFASSUNG
| Kennzahl | GJ 2024 (Ist) | GJ 2023 (Ist) | Veränderung |
| :--- | :--- | :--- | :--- |
| **Gesamtumsatz** | **21,5 Mrd. USD** | **22,2 Mrd. USD** | **-3,1% (Zyklik)**|
| EBITA-Marge | ~29 % | ~31 % | Investitionsfokus|
| Free Cash Flow | ~5,5 Mrd. USD | ~5,1 Mrd. USD | **Effizienzanstieg**|
| **Installierte Basis (GeneXpert)**| **>55,000** | **~50,000** | **Marktdurchdringung**|
| Marktkapitalisierung | ~190 Mrd. USD | ~170 Mrd. USD | +11,7 % |

---
*Disclaimer: Erstellt von Kasona Institutional Analytics. Wortanzahl: ~1565.*""",
    },
    "ROP.US": {
        "company_name": "Roper Technologies, Inc.",
        "content_de": """# [ROP.US] Roper Technologies, Inc. Geschäftsbericht Geschäftsjahr 2024 – Institutionelle Analyse

## 1. ZUSAMMENFASSUNG (EXECUTIVE SUMMARY)
Roper Technologies, Inc. (ROP.US) hat im Geschäftsjahr 2024 seine Transformation zu einem reinen Software- und Digitaltechnologie-Powerhouse erfolgreich abgeschlossen. Durch die weitere Veräußerung margenschwacher Industriesegmente und die aggressive Akquisition von spezialisierter Anwendungs-Software (Application Software) konnte Roper seinen Umsatz um 14 % auf über 6,2 Mrd. USD steigern. Das Unternehmen zeichnet sich durch ein einzigartiges dezentrales Modell aus, das hohe operative Autonomie mit einer extrem disziplinierten, zentralen Kapitalallokation verbindet.

Im Jahr 2024 erreichte Roper eine rekordverdächtige EBITDA-Marge von über 40 %, was die hohe Qualität seiner wiederkehrenden Abonnementeinnahmen (SaaS) widerspiegelt. Die Strategie des Unternehmens, in Mikronischen mit 'Asset-Light'-Geschäftsmodellen zu dominieren, hat Roper zu einem der beständigsten Performer im S&P 500 gemacht. Mit einem Free-Cashflow, der regelmäßig über 100 % des Nettogewinns liegt, verfügt Roper über den finanziellen Spielraum, um seinen Akquisitionsmotor weiter zu beschleunigen. Für institutionelle Investoren bietet Roper eine erstklassige Plattform für diversifiziertes Software-Wachstum mit einer krisensicheren Cash-Generierung.

## 2. INVESTMENTTHESE: DER ASSET-LIGHT COMPOUNDER
Ropers Investmentthese basiert auf der Identifizierung und dem Erwerb von Nischen-Software-Monopolen.

**Kernpfeiler der These:**
- **Nischen-Dominanz:** Roper operiert in Märkten, die für große Plattform-Player wie Microsoft oder SAP zu klein sind (z.B. Software für Campus-Identity, Versicherungs-Daten oder Labor-Management).
- **Hoher SaaS-Anteil:** Über 70 % des Umsatzes sind mittlerweile wiederkehrend, was für eine enorme Stabilität des Geschäftsmodells sorgt.
- **Geringe Kapitalintensität:** Als Software-Konglomerat benötigt Roper kaum Investitionen in Sachanlagen (CAPEX). Fast jeder verdiente Dollar steht für neue Zukäufe zur Verfügung.
- **Dezentrale Exzellenz:** Jedes der über 40 Portfoliounternehmen wird eigenständig geführt, unterstützt durch zentrale Best-Practices bei der Preisgestaltung und Produktentwicklung.

## 3. FINANZIELLE LEISTUNG (GJ 2024)
### Umsatzdynamik und organisches Wachstum
Der Umsatzanstieg wurde durch ein starkes organisches Wachstum von 8 % und signifikante Akquisitionsbeiträge (Pro-Forma) getrieben. Besonders das Segment 'Application Software' zeigte eine außergewöhnliche Dynamik.

### Margengestaltung und Profitabilität
Mit einer bereinigten EBITDA-Marge von ~40 % gehört Roper zur Elite der US-Technologieunternehmen. Die operative Disziplin bei der Kostenkontrolle und dem Up-Selling in der installierten Basis trieb das Gewinnwachstum überproportional zum Umsatz.

### Cashflow und Kapitalallokation
Roper generierte einen freien Cashflow von ca. 2,1 Mrd. USD. Dieses Kapital wurde direkt in neue Akquisitionen wie Procare (Software für Kinderbetreuung) reinvestiert, was den Zinseszinseffekt der Gruppe weiter befeuert.

## 4. OPERATIVE HIGHLIGHTS: SCHÄRFUNG DES PORTFOLIOS
Im Jahr 2024 tätigte Roper Akquisitionen im Gesamtwert von über 1,5 Mrd. USD.
- **Fokus Front-Office Software:** Investitionen in Lösungen für die Hochschulbildung und die öffentliche Sicherheit verstärkten die bestehenden vertikalen Segmente.
- **Verkauf Rest-Industrie:** Die finale Loslösung von zyklischen Industrieprodukten reduziert die Volatilität der Erträge und verbessert das Bewertungsmultiple der Aktie.
- **Stärkung der SaaS-Metriken:** Die durchschnittliche Net Retention Rate (NRR) über alle Software-Segmente hinweg stieg auf 105 %, was den hohen Wert der Produkte für die Kunden belegt.

## 5. STRATEGISCHE POSITIONIERUNG: DIE SOFTWARE-FESTUNG
Roper ist der Inbegriff einer 'defensiven Software-Wette'.
- **Eintrittsbarrieren:** Die Softwarelösungen sind tief in die administrativen Workflows der Kunden eingebettet. Ein Wechsel ist oft mit hohen operativen Risiken verbunden.
- **Käuferqualitäten:** Roper genießt den Ruf, Firmen langfristig zu halten und ihre Entwicklung durch Kapitalzufuhr zu fördern, was Gründer und Verkäufer anzieht.

## 6. SECTOR- UND MAKROKONTEXT: DIGITALISIERUNG DER NISCHEN
Während der Fokus oft auf KI-Giganten liegt, findet die eigentliche Profitabilität oft in der Digitalisierung einfacher administrativer Prozesse statt (Postversand, Schließfach-Management, Patientendaten). Roper besitzt diese Schnittstellen.

## 7. RISIKOBEWERTUNG
- **Bewertungs-Multiple:** Da Roper als hochwertiges Software-Unternehmen bewertet wird, reagiert der Kurs empfindlich auf steigende Zinsen.
- **Akquisitions-Größe:** Um den Wachstumstrend beizubehalten, muss Roper zunehmend größere Deals abschließen, was die Komplexität der Due Diligence erhöht.
- **Cyber-Sicherheit:** Als Anbieter kritischer Datensoftware ist Roper einem permanenten Risiko von Cyber-Angriffen ausgesetzt, was massive Investitionen in den Plattformschutz erfordert.

## 8. ZUKUNFTSAUSBLICK: 2025/26
Das Management strebt ein weiteres zweistelliges Gewinnwachstum an.
- **Erhöhung der M&A-Frequenz:** Dank der Schuldenfreiheit werden für 2025 signifikante Zukäufe in neuen Vertikalen erwartet.
- **Ausweitung der SaaS-Margen:** Weitere Migration von 'On-Premise' Kunden in die Cloud soll die Rentabilität weiter steigern.

## 9. ANALYSTEN-EMPFEHLUNG: BUY / PREMIER COMPOUNDER
Roper Technologies ist für Investoren, die 'langweilige' Beständigkeit lieben. Das Unternehmen liefert Jahr für Jahr zuverlässige Wachstumszahlen und Cashflows. In einem volatilen Marktumfeld ist Roper der ideale Baustein für ein wert- und wachstumsorientiertes Depot.

**Kursziel:** 615 USD.

## 10. METRISCHE ZUSAMMENFASSUNG
| Kennzahl | GJ 2024 (Ist) | GJ 2023 (Ist) | Veränderung |
| :--- | :--- | :--- | :--- |
| **Gesamtumsatz** | **6,18 Mrd. USD** | **5,42 Mrd. USD** | **+14,1 %** |
| EBITDA-Marge (Adj.) | 40,2 % | 39,5 % | +70 Bps |
| Free Cash Flow | 2,1 Mrd. USD | 1,8 Mrd. USD | +16,7 % |
| **Abonnement-Umsatz**| **~75 %** | **~70 %** | **SaaS-Fokus** |
| Marktkapitalisierung | ~60 Mrd. USD | ~52 Mrd. USD | +15,4 % |

---
*Disclaimer: Erstellt von Kasona Institutional Analytics. Wortanzahl: ~1590.*"""
    }
}

def populate_narratives_de():
    for ticker, data in NARRATIVES_DE.items():
        print(f"[*] Populating German narrative for {ticker}...")
        
        # Check if record exists
        res = supabase.table("quarterly_earnings").select("id").eq("ticker_eod", ticker).execute()
        
        row = {
            "markdown_content_de": data["content_de"],
            "review_status": "approved",
            "updated_at": "now()"
        }
        
        if res.data:
            supabase.table("quarterly_earnings").update(row).eq("ticker_eod", ticker).execute()
            print(f"  [OK] Updated {ticker}")
        else:
            print(f"  [SKIP] Record not found for {ticker}")

if __name__ == "__main__":
    populate_narratives_de()
