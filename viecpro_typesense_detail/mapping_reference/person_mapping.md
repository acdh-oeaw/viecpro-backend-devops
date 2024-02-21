# detail pages


# person 

header: REL = "relation", "ziel", "von", "bis"
## sections

### stammdaten 

### potentielle dubletten 
- data: personRelData['Dubletten Beziehung']
- headers: REL

### alternative namensschreibweisen 
- data: labelData.alt_names
- array !

### adelsstand und ausszeichnungen
- data: labelData.collected_titles
- array !

### akademische titel 
- data: labelData.title_academic
- array !

### download und zitierweise
- ?

### quellenbelege
- data: referencesData
- array ?
- parses url references into links and others into list items

### funktionen am hof
- data: relData.PersonInstitution
- headers: "Bezeichnung", "Institution", "Von", "Bis"

### personenbeziehungen am hof
- data: personRelData["Berufliche Beziehung"]
- header: REL

### sonstiger bezug zum hof
- data: labelData.court_other
- array !

### ehe und verwandschaftsverhältnisse
- data: personRelData["Verwandtschaftliche Beziehung"]
- headers: REL

### bezug zu kirche und orden 
- data: relData["Kirchl. Amtsbeziehung"] AND labelData.church_and_o
- headers: REL

### sonstige tätigkeiten 
- data: labelData.other_jobs
- headers: REL


```javascript

   if (check(lt, 'Konfession')) {
      res.religion = l.name;
    }
    if (check(lt, 'Adelstitel')) {
      res.collected_titles.push({ name: l.name, start_date: l.start_date, end_date: l.end_date });
    }
    if (check(lt, 'verheiratet')) {
      res.married_name.push({ name: l.name, start_date: l.start_date, end_date: l.end_date });
    }
    if (check(lt, 'Nachname verheiratet (1. Ehe')) {
      res.first_marriage = l.name;
    }
    if (check(lt, 'Sonstiger Hofbezug')) {
      res.court_other.push({ name: l.name, start_date: l.start_date, end_date: l.end_date });
    }
    if (check(lt, 'Akade')) {
      res.title_academic.push({ name: l.name, start_date: l.start_date, end_date: l.end_date });
    }
    if (check(lt, 'Funktion, Amtsinhabe und Beruf')) {
      res.other_jobs.push({ name: l.name, start_date: l.start_date, end_date: l.end_date });
    }
    if (check(lt, 'Stand')) {
      res.collected_titles.push({ name: l.name, start_date: l.start_date, end_date: l.end_date });
    }
    if (check(lt, 'Auszeichnung')) {
      res.collected_titles.push({ name: l.name, start_date: l.start_date, end_date: l.end_date });
    }
    if (check(lt, 'Kirche')) {
      res.church_and_o.push({ name: l.name, start_date: l.start_date, end_date: l.end_date });
    }
    if (check(lt, 'Orden')) {
      res.church_and_o.push({ name: l.name, start_date: l.start_date, end_date: l.end_date });
    }

```
# institution 


# place


# event


# work 


# court


# sources