## Anomaly detection

Sve provjere izvode se periodički svakih POLL_INTERVAL(=15) sekundi. 

### Flapping
Anomalija: korisnik/uređaj se prebacuje između dva BTS-a vise od 5 puta na sat. \
Iz BTS_records tablice uzimaju se svi zapisi kojima je 'timestamp_arrival' unutar sat vremena od trenutka dohvaćanja podataka iz baze. 
Zapisi se grupiraju prema IMEI brojevima. Prema zapisima s istim IMEI brojem prati se kretanje korisnika/uređaja u zadnjih sat vremena;
svaki BTS zapis pomoću polja 'bts_id' i 'previous_bts_id' bilježi prijelaz između dva BTS-a. 

U algoritmu za traženje flappinga za svaki prijelaz zapisuje se niz idućih prijelaza; niz se nadopunjava dok god se izmjenjuju samo dva BTS_id-a; kad se pojavi treći BTS_id, niz se prekida. 

Ovdje je ilustriran primjer kretanja jednog korisnika:
```
BTS3-> BTS2-> BTS1-> BTS2-> BTS1-> BTS2-> BTS1-> BTS2-> BTS3-> BTS2-> BTS4
     3      2      1      2      1      2      1      2      3      2
     2      1      2      1      2      1      2      3      2      4
            2      1      2      1      2             2
            1      2      1      2
            2      1      2
            1      2
            2            
           !!!
```
U gornjem primjeru došlo je do flappinga između BTS2 i BTS1, zabilježeno je 6 prijelaza (jedna strelica = jedan prijelaz: 2->1->2->1->2->1->2). 
Za nizove duže od 5 prijelaza generira se alert, ali ignorira se svaki niz koji je kraći od svog neposrednog prethodnika jer se radi o podnizu dužeg niza. 
Za gornji primjer koji je nastao od 10 CDR zapisa generirao bi se jedan alert.

### Abnormal speed
Anomalija: korisnik/uređaj se korisnik se kreće brzinom većom od 200 km/h. \
Svaki CDR zapis ima polja 'distance' i 'duration', prema kojima se računa brzina u km/h. Ako je zabilježena brzina veća od 200 km/h, generira se alert. Provjeravaju se svi zapisi dodani u tablicu u zadnjih POLL_INTERVAL sekundi, tj. nakon zadnje provjere.

### Overload
Anomalija: na BTS je spojeno više od 50 uređaja. \
Za provjeru preopterećenja BTS-a provjerava se BTS_registry tablica, dohvaćaju se zapisi kojima je vrijednost u polju 'current_load' veća od 50. 
Provjeravaju se samo zapisi koji su ažurirani nakon zadnje provjere, tj. uzimaju se samo zapisi kojima je updated_at timestamp unutar POLL_INTERVAL sekundi od trenutka provjere. 

Za svaku detektiranu anomaliju generira se alert s poljima (alert_type, severity, imei, bts_id, description, detected_at) i pohranjuje se u alerts tablicu. 
