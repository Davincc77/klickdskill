# Référentiels de Compétences Mondiaux — Champ `occupational_competencies` pour .klickd v3.3

> **Document de référence technique** — Luxlearn.app / klickd.app  
> Objectif : Définir le champ universel `occupational_competencies` pour le format .klickd v3.3, couvrant TOUS les postes de travail, du politicien à l'éboueur.  
> Date de production : 2025

---

## Contexte : Le format .klickd actuel

Le format `.klickd` est un standard ouvert de continuité de contexte pour agents IA, généré en local sur l'appareil de l'utilisateur à la fin de chaque session avec l'assistant Kai (klickd.app). Il contient actuellement :

- **Ce que l'utilisateur maîtrise** (`mastered`)
- **Ce qui accroche** / en difficulté (`struggles`)
- **Style d'apprentissage** de l'utilisateur

Le format est centré sur l'apprentissage scolaire (programmes nationaux, 7 pays, 4 matières). L'extension v3.3 vise à l'universaliser pour couvrir **toutes les compétences professionnelles**, tous secteurs confondus.

---

## Section 1 — Inventaire exhaustif des référentiels mondiaux

### 1.1 Référentiels européens

---

#### ESCO v1.2.1 — European Skills, Competences, Qualifications and Occupations

| Champ | Détail |
|---|---|
| **Organisme** | Commission européenne (DG EMPL) |
| **Pays/Région** | Union européenne (28 langues) |
| **URL officielle** | https://esco.ec.europa.eu |
| **Version actuelle** | v1.2.1 (décembre 2025) |
| **Structure** | 3 piliers : Occupations / Skills & Competences / Qualifications |
| **Taxonomie Skills** | 4 sous-classifications : Knowledge · Language skills · Skills · Transversal skills |
| **Occupations couvertes** | ~3 000 occupations (alignées ISCO-08) |
| **Compétences couvertes** | ~13 939 concepts de compétences et connaissances |
| **Niveaux** | Aligné EQF 1–8 |
| **Disponible JSON/API** | **OUI** — CSV, JSON-LD, ODS, RDF/TTL, XML + API REST publique |
| **API endpoint** | `https://ec.europa.eu/esco/api/` |
| **Licence** | CC BY 4.0 — gratuit, libre d'utilisation |
| **Cas d'usage .klickd** | Référence primaire pour `occupation_code` et `competency.id`. Utiliser les URIs ESCO natifs (ex: `http://data.europa.eu/esco/skill/S4.5.1`). La relation occupation↔skill est exploitable directement via API pour auto-suggérer des compétences à partir du titre de poste. |

**Structure d'un concept ESCO :**
```json
{
  "uri": "http://data.europa.eu/esco/skill/b89e5af8-3f5f-4cf3-b4d0-27de7d76a4d2",
  "title": "machine learning",
  "type": "skill/competence",
  "broader": ["http://data.europa.eu/esco/skill/..."],
  "relatedOccupations": ["data scientist", "AI engineer"]
}
```

---

#### EQF — European Qualifications Framework

| Champ | Détail |
|---|---|
| **Organisme** | Commission européenne |
| **URL officielle** | https://europass.europa.eu/en/description-eight-eqf-levels |
| **Structure** | 8 niveaux de qualification (learning outcomes) |
| **Taxonomie** | Chaque niveau défini par : Knowledge · Skills · Responsibility & Autonomy |
| **Couverture** | Tous types de qualifications (enseignement primaire → doctorat) |
| **Disponible JSON/API** | Partiel — données dans Europass et ESCO |
| **Cas d'usage .klickd** | Niveau de maîtrise universel (`level` 1–8) applicable à n'importe quelle compétence. EQF 1 = basique, EQF 8 = expert mondial. Utilisable comme échelle de progression cross-frameworks. |

**Correspondances EQF :**

| EQF | Descripteur | Équivalent |
|---|---|---|
| 1 | Connaissances générales de base | Primaire |
| 2 | Connaissances factuelles de base | Collège |
| 3 | Connaissances de faits, principes et concepts | CAP/BEP |
| 4 | Connaissances théoriques et factuelles larges | Bac |
| 5 | Connaissances spécialisées complètes | BTS/DUT |
| 6 | Connaissances avancées d'un domaine | Licence |
| 7 | Connaissances hautement spécialisées | Master |
| 8 | Frontière de la connaissance | Doctorat/Expert mondial |

---

#### DigComp 3.0 — European Digital Competence Framework

| Champ | Détail |
|---|---|
| **Organisme** | JRC (Joint Research Centre), Commission européenne |
| **URL officielle** | https://joint-research-centre.ec.europa.eu/digcomp_en |
| **Version** | 3.0 (2022) |
| **Structure** | 5 domaines de compétence, 21 compétences |
| **5 domaines** | Information & data literacy · Communication & collaboration · Digital content creation · Safety · Problem solving |
| **Niveaux** | 8 niveaux de maîtrise (Foundation → Highly Specialised) |
| **Couverture** | Tous citoyens, tous âges, tous contextes |
| **Disponible JSON/API** | Partiellement — PDF officiel, données dans ESCO pour les skills digitaux |
| **Cas d'usage .klickd** | Composant clé pour les compétences numériques universelles. Peut s'appliquer à n'importe quel poste (éboueur avec app de collecte → DigComp niveau 1-2, Data Scientist → niveau 7-8). |

---

#### DigCompEdu — Digital Competence Framework for Educators

| Champ | Détail |
|---|---|
| **Organisme** | JRC, Commission européenne |
| **URL officielle** | https://joint-research-centre.ec.europa.eu/digcompedu_en |
| **Structure** | 6 domaines, 22 compétences |
| **6 domaines** | Professional engagement · Digital resources · Teaching & learning · Assessment · Empowering learners · Facilitating learners' digital competence |
| **Niveaux** | 6 niveaux (A1 Newcomer → C2 Pioneer) |
| **Outil d'auto-évaluation** | SELFIEforTEACHERS (24 langues officielles EU) |
| **Disponible JSON/API** | Non — PDF et outil en ligne uniquement |
| **Cas d'usage .klickd** | Référentiel dédié aux enseignants. Complète DigComp pour le contexte pédagogique. |

---

#### EntreComp — Entrepreneurship Competence Framework

| Champ | Détail |
|---|---|
| **Organisme** | JRC + DG Employment, Commission européenne |
| **URL officielle** | https://joint-research-centre.ec.europa.eu/entrecomp-entrepreneurship-competence-framework_en |
| **Version** | 2016 (toujours référence) |
| **Structure** | 3 domaines, 15 compétences, 8 niveaux de progression (Novice → Expert) |
| **3 domaines** | Ideas & Opportunities · Resources · Into Action |
| **15 compétences** | Spotting opportunities, Creativity, Vision, Valuing ideas, Ethical thinking, Self-awareness, Motivation & perseverance, Mobilising others, Taking initiative, Planning & management, Coping with uncertainty, Working with others, Learning through experience… |
| **Couverture** | Compétences entrepreneuriales, applicables à tout rôle |
| **Disponible JSON/API** | Non — PDF officiel |
| **Cas d'usage .klickd** | Référentiel pour politiciens, managers, créateurs de startup, artisans indépendants. |

---

#### LifeComp — Personal, Social & Learning to Learn Competence

| Champ | Détail |
|---|---|
| **Organisme** | JRC, Commission européenne |
| **URL officielle** | https://joint-research-centre.ec.europa.eu/lifecomp_en |
| **Publication** | 2020 |
| **Structure** | 3 domaines, 9 compétences |
| **3 domaines** | Personal · Social · Learning to learn |
| **9 compétences** | Self-regulation, Flexibility/adaptability, Wellbeing · Empathy, Communication, Collaboration · Growth mindset, Critical thinking, Managing learning |
| **Couverture** | Compétences personnelles et sociales, lifelong learning |
| **Disponible JSON/API** | Non — PDF officiel uniquement |
| **Cas d'usage .klickd** | Soft skills universels : applicable à tous les postes. Les compétences comme empathie (soignants), collaboration (chirurgiens), gestion du stress (éboueurs en conditions difficiles). |

---

#### GreenComp — European Sustainability Competence Framework

| Champ | Détail |
|---|---|
| **Organisme** | JRC, Commission européenne (Green Deal) |
| **URL officielle** | https://joint-research-centre.ec.europa.eu/greencomp-european-sustainability-competence-framework_en |
| **Publication** | Janvier 2022 |
| **Structure** | 4 domaines, 12 compétences |
| **4 domaines** | Embodying sustainability values · Embracing complexity · Envisioning sustainable futures · Acting for sustainability |
| **12 compétences** | Valuing sustainability, Supporting fairness, Promoting nature, Systems thinking, Critical thinking, Problem framing, Futures literacy, Adaptability, Exploratory thinking, Political agency, Collective action, Individual initiative |
| **Couverture** | Durabilité environnementale, applicable à tous secteurs |
| **Disponible JSON/API** | Non — PDF officiel |
| **Cas d'usage .klickd** | Crucial pour éboueurs (gestion des déchets, tri sélectif, économie circulaire), agriculteurs, politiciens environnementaux. |

---

### 1.2 Référentiels américains

---

#### O*NET — Occupational Information Network

| Champ | Détail |
|---|---|
| **Organisme** | US Department of Labor / Employment and Training Administration |
| **URL officielle** | https://www.onetonline.org / https://www.onetcenter.org |
| **Structure** | Content Model à 6 domaines, taxonomie O*NET-SOC |
| **6 domaines** | Worker Characteristics · Worker Requirements · Experience Requirements · Occupational Requirements · Workforce Characteristics · Occupation-Specific Info |
| **Occupations couvertes** | 1 016 titres (923 avec données complètes), représentant +55 000 emplois US |
| **Descripteurs** | 277 descripteurs, 19 000+ task statements, 2 000+ detailed work activities |
| **Niveaux** | Job Zones 1–5 (niveau éducation/expérience requis) |
| **Disponible JSON/API** | **OUI** — O*NET Web Services API (REST/JSON), téléchargement CSV/Excel |
| **API endpoint** | `https://services.onetcenter.org/ws/` |
| **Licence** | Domaine public US — libre d'utilisation |
| **Cas d'usage .klickd** | Référence primaire pour le marché nord-américain. Code O*NET-SOC (ex: `11-1011.00` = Chief Executives) utilisable comme `occupation_code`. Crosswalk disponible vers ISCO-08 et ESCO. |

**Extrait Content Model :**
```
Worker Requirements:
  ├── Skills (35 skills: active listening, critical thinking, coordination...)
  ├── Knowledge (33 knowledge areas: mathematics, psychology, law...)
  ├── Education (educational requirements)
  └── Credentials (certifications, licences)
```

---

#### DOL/ETA Competency Models

| Champ | Détail |
|---|---|
| **Organisme** | US Department of Labor, Employment & Training Administration |
| **URL officielle** | https://www.careeronestop.org/CompetencyModel/ |
| **Structure** | Tier-based pyramid model (Foundational → Industry-specific → Occupation-specific) |
| **Couverture** | 20+ secteurs industriels avec modèles spécifiques |
| **Niveaux** | Tiers 1-9 (Personal effectiveness → Management) |
| **Disponible JSON/API** | Partiellement — via CareerOneStop API |
| **Cas d'usage .klickd** | Modèles sectoriels pour IT, Healthcare, Manufacturing, Agriculture, Construction... Utile pour définir les compétences par cluster sectoriel. |

---

#### NACE — Career Readiness Competencies

| Champ | Détail |
|---|---|
| **Organisme** | National Association of Colleges and Employers |
| **URL officielle** | https://www.naceweb.org/career-readiness/competencies/career-readiness-defined/ |
| **Version** | Révisé avril 2024 |
| **Structure** | 8 compétences transversales |
| **8 compétences** | Career & Self-Development · Communication · Critical Thinking · Equity & Inclusion · Leadership · Professionalism · Teamwork · Technology |
| **Couverture** | Diplômés universitaires entrant dans la vie professionnelle |
| **Disponible JSON/API** | Non — PDF officiel |
| **Cas d'usage .klickd** | Soft skills transversaux pour tout professionnel. Particulièrement utile pour les jeunes entrant sur le marché du travail. |

---

#### SCANS — Secretary's Commission on Achieving Necessary Skills

| Champ | Détail |
|---|---|
| **Organisme** | US Department of Labor (1992, toujours référencé) |
| **URL officielle** | https://wdr.doleta.gov/SCANS/ |
| **Structure** | 5 compétences + 3 fondations (SCANS Foundation) |
| **5 compétences** | Resources · Interpersonal · Information · Systems · Technology |
| **3 fondations** | Basic skills · Thinking skills · Personal qualities |
| **Couverture** | Employabilité générale, milieu professionnel US |
| **Disponible JSON/API** | Non — document historique de référence |
| **Cas d'usage .klickd** | Fondation conceptuelle pour les compétences de base en milieu de travail. Utilisé comme référence pour les niveaux d'entrée. |

---

### 1.3 Référentiels asiatiques et Pacifique

---

#### NCS — National Competency Standards (Corée du Sud)

| Champ | Détail |
|---|---|
| **Organisme** | Ministry of Employment and Labor / HRD Korea |
| **URL officielle** | https://www.ncs.go.kr / https://www.hrdkorea.or.kr/ENG/8/1 |
| **Structure** | 4 niveaux hiérarchiques : 24 Major Groups → 80 Sub-Major → 226 Minor → 880 Unit Groups |
| **Couverture** | 880 types d'emplois (job types) dans tous les secteurs |
| **Niveaux** | 8 niveaux (Level 1 → Level 8), alignés sur EQF |
| **Composants par unité** | Competency unit elements + Performance criteria + Knowledge/Technology/Attitude |
| **Disponible JSON/API** | Partiellement — données accessibles via portail national |
| **Cas d'usage .klickd** | Référence pour le marché coréen. Structure niveaux 1-8 compatible avec EQF. Utile pour les compétences techniques industrielles (construction, manufacturing). |

---

#### SkillsFuture — Skills Framework (Singapour)

| Champ | Détail |
|---|---|
| **Organisme** | SkillsFuture Singapore (SSG) |
| **URL officielle** | https://www.skillsfuture.gov.sg/skills-framework |
| **Développement** | Co-créé avec employeurs, associations industrielles, établissements d'enseignement, syndicats, gouvernement |
| **Structure** | Informations sectorielles + Parcours de carrière + Rôles/occupations + Skills requises (existantes et émergentes) |
| **Couverture** | Tous secteurs majeurs de l'économie singapourienne (ICT, Social Service, Retail, Hospitality, Logistics...) |
| **Disponible JSON/API** | Non — portail web sectoriel |
| **Cas d'usage .klickd** | Modèle de co-création employeur-institution exemplaire. Framework ICT de Singapour (IMDA) dispose de career maps détaillées. |

---

#### NOS — National Occupational Standards (Chine)

| Champ | Détail |
|---|---|
| **Organisme** | Ministry of Human Resources and Social Security (MOHRSS) |
| **URL officielle** | http://www.mohrss.gov.cn |
| **Structure** | Directoire national des certifications professionnelles (mis à jour régulièrement) |
| **Couverture** | 347 nouvelles occupations reconnues récemment (livreur, administrateur cybersécurité, futures trader...) |
| **Catégories** | Licensing (entrée obligatoire) + Certification (skill-level assessment volontaire) |
| **Niveaux** | 5 niveaux de skill (初级/Junior → 高级技师/Senior Technician) |
| **Disponible JSON/API** | Non — données gouvernementales fragmentées |
| **Cas d'usage .klickd** | Marché chinois : 894 occupations obsolètes supprimées, 347 nouvelles créées entre 2013-2021. Référence pour les compétences d'économie numérique (gig economy, plateformes). |

---

#### METI Digital Skills Standards (Japon)

| Champ | Détail |
|---|---|
| **Organisme** | Ministry of Economy, Trade and Industry (METI) |
| **URL officielle** | https://www.meti.go.jp/english/ |
| **Documents clés** | "Approaches to human resources and skills required for DX" (2023) · Digital Governance Code 3.0 (2024) |
| **Structure** | Compétences DX (Digital Transformation) par profil professionnel |
| **Compétences émergentes** | Prompt engineering · Generative AI evaluation · Japanese language skills for AI |
| **Disponible JSON/API** | Non — PDF gouvernemental |
| **Cas d'usage .klickd** | Référence pour compétences IA/DX dans contexte japonais. Notion de "cliff 2025" (pénurie de compétences digitales) justifie l'urgence de tracking des skills numériques. |

---

#### AQF — Australian Qualifications Framework

| Champ | Détail |
|---|---|
| **Organisme** | Australian Government (Department of Education) |
| **URL officielle** | https://www.aqf.edu.au |
| **Version** | 2e édition, janvier 2013 (révision en cours) |
| **Structure** | 10 niveaux de qualification (Certificate I → Doctoral Degree) |
| **Secteurs couverts** | Enseignement secondaire + Vocational Education & Training (VET) + Higher Education |
| **Training Packages** | Développés par Jobs and Skills Councils (JSC) par secteur industriel |
| **Codes** | Units of Competency avec codes standardisés (ex: SIFCBCR002) |
| **Disponible JSON/API** | **OUI** — Training.gov.au dispose d'une API (https://training.gov.au) |
| **Cas d'usage .klickd** | Référence pour l'océan Pacifique et Commonwealth. Training packages couvrent des métiers très spécifiques (y compris funeral operations, agriculture, construction). Compatible avec NVQ UK. |

---

### 1.4 Référentiels internationaux

---

#### ISCO-08 — International Standard Classification of Occupations

| Champ | Détail |
|---|---|
| **Organisme** | ILO (International Labour Organization) |
| **URL officielle** | https://ilostat.ilo.org/methods/concepts-and-definitions/classification-occupation/ |
| **Version** | ISCO-08 (4e révision, remplace ISCO-88) |
| **Structure** | 4 niveaux hiérarchiques : 10 Major Groups → 43 Sub-major → 130 Minor → 436 Unit groups |
| **Couverture** | Tous emplois mondiaux, tous pays |
| **2 dimensions de skill** | Skill level (4 niveaux ISCO) · Skill specialization (field/tools/materials/goods) |
| **4 skill levels** | Élémentaire (ISCO 1) → Opérateur (ISCO 2) → Technicien (ISCO 3) → Professionnel/Manager (ISCO 4) |
| **Disponible JSON/API** | **OUI** — ILOSTAT API publique (https://ilostat.ilo.org/resources/ilostat-r-package/) |
| **Licence** | Libre d'utilisation |
| **Cas d'usage .klickd** | **Référentiel d'occupation universel** — doit être la colonne vertébrale de `occupation_code`. Crosswalk vers ESCO, O*NET, NCS disponibles. L'éboueur = ISCO 9121 (Refuse Workers), le chirurgien = ISCO 2212 (Specialist Medical Practitioners). |

**Structure ISCO-08 :**
```
Major Group 1: Managers
Major Group 2: Professionals
Major Group 3: Technicians & Associate Professionals
Major Group 4: Clerical Support Workers
Major Group 5: Service & Sales Workers
Major Group 6: Skilled Agricultural Workers
Major Group 7: Craft & Related Trades Workers
Major Group 8: Plant & Machine Operators
Major Group 9: Elementary Occupations (incl. refuse workers)
Major Group 0: Armed Forces
```

---

#### UNESCO ISCED — International Standard Classification of Education

| Champ | Détail |
|---|---|
| **Organisme** | UNESCO |
| **URL officielle** | http://uis.unesco.org/en/topic/international-standard-classification-education-isced |
| **Version** | ISCED 2011 (niveaux) + ISCED-F 2013 (domaines) |
| **Structure** | 9 niveaux d'éducation (0 = Petite enfance → 8 = Doctorat) |
| **Couverture** | Classification internationale des niveaux d'enseignement |
| **Disponible JSON/API** | **OUI** — UIS Data API (http://data.uis.unesco.org/) |
| **Cas d'usage .klickd** | Niveau d'éducation requis pour une occupation. Complémentaire à EQF pour les contextes hors-Europe. |

---

#### OECD Skills Outlook

| Champ | Détail |
|---|---|
| **Organisme** | OCDE |
| **URL officielle** | https://www.oecd.org/en/about/projects/future-of-education-and-skills-2030.html |
| **Version** | Skills Outlook 2025 |
| **Structure** | 3 compétences-clés du 21e siècle + compétences socio-émotionnelles |
| **3 compétences-clés** | Literacy · Numeracy · Adaptive problem-solving |
| **Compétences socio-émotionnelles** | Conscientiousness · Emotional stability · Open-mindedness · Perseverance |
| **Cadre Learning Compass 2030** | Student Agency + Core Foundations + Transformative Competencies |
| **Disponible JSON/API** | **OUI** — OECD iLibrary API (https://www.oecd-ilibrary.org/statistics) |
| **Cas d'usage .klickd** | Framework analytique pour mesurer les compétences du 21e siècle. "Adaptive problem solving" est particulièrement pertinent pour les métiers en mutation rapide. |

---

#### ITU Digital Skills Assessment Framework

| Champ | Détail |
|---|---|
| **Organisme** | International Telecommunication Union (ITU) |
| **URL officielle** | https://academy.itu.int/research-advocacy-and-convening-platforms/research-publications/digital-skills-assessment-guidebook |
| **Publication** | ITU Academy Digital Skills Assessment Guidebook |
| **Structure** | 5 chapitres : Supply assessment → Demand assessment → Mismatch → Anticipation → Conclusions |
| **Couverture** | Évaluation nationale des compétences numériques |
| **Disponible JSON/API** | Non — guidebook PDF |
| **Cas d'usage .klickd** | Framework pour évaluer et anticiper les besoins en compétences numériques au niveau national. Complément à DigComp pour les pays hors-UE. |

---

### 1.5 Référentiels sectoriels

---

#### ICN — International Council of Nurses Competency Framework

| Champ | Détail |
|---|---|
| **Organisme** | International Council of Nurses (ICN) |
| **URL officielle** | https://www.icn.ch |
| **Documents** | ICN Nursing Care Continuum Framework · ICN Core Competencies in Disaster Nursing v2.0 (2019) |
| **Structure** | 3 domaines principaux → 15+ sous-domaines de compétences |
| **3 domaines** | Professional, Ethical & Legal Practice · Care Provision & Management · Professional, Personal & Quality Development |
| **Niveaux** | 5 niveaux de personnel infirmier (Support Worker → Advanced Practice Nurse) |
| **Compétences clés** | Accountability · Ethical Practice · Assessment · Planning · Implementation · Evaluation · Therapeutic Communication · Leadership · Delegation · Safe Environment |
| **Couverture** | 129 pays membres ICN |
| **Disponible JSON/API** | Non — PDF officiel |
| **Cas d'usage .klickd** | Référentiel infirmier universel. Les compétences physiques (gestes techniques), relationnelles (communication thérapeutique), et éthiques sont toutes représentées. |

---

#### WHO Global Competency & Outcomes Framework (Healthcare Workers)

| Champ | Détail |
|---|---|
| **Organisme** | World Health Organization (WHO) |
| **URL officielle** | https://www.who.int/publications/i/item/9789240029200 |
| **Publication** | 2022 |
| **Structure** | Framework compétences-résultats pour les travailleurs de santé |
| **Couverture** | Formation des soignants mondiaux, Universal Health Coverage |
| **Disponible JSON/API** | Non — PDF officiel |
| **Cas d'usage .klickd** | Complément ICN pour tous les professionnels de santé (médecins, sages-femmes, agents de santé communautaire). |

---

#### DigCompEdu + UNESCO ICT CFT — Enseignants

| Champ | Détail |
|---|---|
| **Organisme** | UNESCO |
| **URL officielle** | https://www.unesco.org/en/articles/ai-competency-framework-teachers |
| **Structure UNESCO ICT CFT** | 3 étapes (Knowledge acquisition → Knowledge deepening → Knowledge creation) × 7 niveaux |
| **AI Competency Framework** | 2025 — Compétences IA spécifiques aux enseignants |
| **Couverture** | Aligné Agenda 2030, applicable mondialement |
| **Disponible JSON/API** | Non — PDF et portail UNESCO |
| **Cas d'usage .klickd** | DigCompEdu (EU) + UNESCO ICT CFT (mondial) = référentiel complet pour enseignants. |

---

#### NVQ — National Vocational Qualifications (Royaume-Uni)

| Champ | Détail |
|---|---|
| **Organisme** | Ofqual / awarding bodies (City & Guilds, BTEC, etc.) |
| **URL officielle** | https://www.gov.uk/national-vocational-qualifications |
| **Structure** | 5 niveaux (Level 1–5) basés sur compétences observées en situation réelle |
| **Évaluation** | Competent / Not Yet Competent (pas de notation) |
| **Secteurs** | Construction · Engineering · Healthcare · IT · Hospitality · Arts · Agriculture · Transport |
| **Couverture** | Tous métiers manuels, techniques et professionnels UK |
| **Disponible JSON/API** | Via Ofqual Register (https://register.ofqual.gov.uk/api) |
| **Cas d'usage .klickd** | Référentiel cols bleus et métiers techniques. Level 3 NVQ Carpentry couvre : techniques avancées de charpente, supervision, sécurité, lecture de plans. |

---

#### FAO / Skills for Agriculture

| Champ | Détail |
|---|---|
| **Organisme** | FAO + CABI (Centre for Agriculture and Bioscience International) |
| **URL officielle** | https://www.cabi.org/products-and-services/academy/skills-framework/ |
| **Structure** | Framework structuré par rôle, niveaux croissants de responsabilité |
| **Compétences couvertes** | Technical skills (precision farming, IoT, drones, irrigation) · Digital literacy (farm management software) · Sustainable practices (climate-smart agriculture, waste management) |
| **Couverture** | Agriculture mondiale, agritech |
| **Disponible JSON/API** | Non |
| **Cas d'usage .klickd** | Référentiel pour agriculteurs de toutes cultures. Couvre les compétences physiques (conduite d'engins, manipulation d'animaux), techniques (agronomie, phytosanitaire) et numériques (precision farming). |

---

#### HSE / WAMITAB — Waste Management & Collection

| Champ | Détail |
|---|---|
| **Organisme** | Health and Safety Executive (UK) + WAMITAB |
| **URL officielle** | https://www.hse.gov.uk/waste/collection.htm |
| **Structure** | Compétences HSE par risque (transport, glissades, machines, violence, dermatoses) |
| **Risques couverts** | Transport · Slips & trips · Falls · Machinery · Violence at work · Dermatitis · Stress |
| **Certificats** | WAMITAB (Waste Management Industry Training Advisory Board) — NVQ Levels 1–4 en gestion des déchets |
| **Disponible JSON/API** | Non |
| **Cas d'usage .klickd** | Compétences HSE/sécurité pour les éboueurs — type `physical` et `safety`. |

---

## Section 2 — Compétences manquantes dans .klickd actuel

Le format .klickd actuel (`mastered` / `in_progress` / `struggles`) est centré sur l'apprentissage scolaire académique. Voici l'analyse des lacunes pour une extension professionnelle universelle.

### 2.1 Tableau des lacunes

| Dimension | Référentiel de référence | Manque dans .klickd actuel | Impact |
|---|---|---|---|
| **Compétences comportementales (soft skills)** | LifeComp, NACE, SCANS | Aucun champ pour empathie, leadership, gestion du stress, communication interpersonnelle | Critique — absent pour 90% des métiers |
| **Compétences techniques métier** | O*NET, ESCO, NCS, NVQ | Les skills académiques ne couvrent pas la conduite d'engins, la chirurgie, la maçonnerie | Critique |
| **Compétences physiques/motrices** | O*NET Abilities, ICN, NVQ | Aucune dimension pour dextérité manuelle, endurance physique, gestes techniques | Critique pour artisans, chirurgiens, éboueurs |
| **Compétences civiques/politiques** | EntreComp (political agency), GreenComp | Aucun référentiel pour compétences législatives, négociation politique, représentation publique | Critique pour élus |
| **Compétences de sécurité/HSE** | HSE UK, OSHA (US), ISO 45001 | Absentes — pourtant obligatoires dans 70% des métiers physiques | Important |
| **Compétences numériques avancées** | DigComp 3.0, ITU | DigComp non intégré dans le format actuel malgré son importance universelle | Important |
| **Compétences linguistiques professionnelles** | CEFR (en partie présent) | CEFR couvre le général mais pas le langage professionnel spécialisé (juridique, médical, technique) | Modéré |
| **Compétences de durabilité** | GreenComp | Absentes — pourtant croissantes dans tous les secteurs | Modéré |
| **Compétences entrepreneuriales** | EntreComp | Absentes — relevant pour auto-entrepreneurs, artisans, farmers | Modéré |
| **Niveaux de maîtrise cross-framework** | EQF, ISCO skill levels | Le système actuel mastered/in_progress/struggles est trop binaire — pas de gradation fine | Important |

### 2.2 Types de compétences à ajouter

```
Taxinomie proposée pour .klickd v3.3 :

type: "knowledge"      → Savoir théorique (déjà partiellement couvert)
type: "skill"          → Savoir-faire pratique (nouveau)
type: "attitude"       → Comportements, valeurs, soft skills (nouveau)
type: "physical"       → Compétences motrices/physiques (nouveau)
type: "safety"         → Compétences HSE, sécurité au travail (nouveau)
type: "civic"          → Compétences civiques, éthiques, politiques (nouveau)
type: "digital"        → Compétences numériques (DigComp) (nouveau, structuré)
type: "language_pro"   → Langage professionnel spécialisé (au-delà CEFR) (nouveau)
type: "sustainability" → Compétences vertes (GreenComp) (nouveau)
```

---

## Section 3 — Proposition du champ `occupational_competencies` v3.3

### 3.1 Schéma JSON complet

```json
{
  "occupational_competencies": {
    "schema_version": "3.3",
    "generated_at": "2025-12-22T10:00:00Z",
    "privacy": "local_only",

    "occupation": {
      "isco_code": "9121",
      "isco_label": "Refuse and Recyclable Material Collectors",
      "esco_uri": "http://data.europa.eu/esco/occupation/...",
      "esco_label": "refuse collector",
      "onet_code": "53-7081.00",
      "onet_label": "Refuse and Recyclable Material Collectors",
      "local_framework": "NVQ|NCS|AQF|SkillsFuture|custom",
      "local_code": "NVQ:L2-WM001",
      "custom_label": null
    },

    "frameworks_referenced": [
      {
        "id": "ESCO",
        "version": "1.2.1",
        "uri": "https://esco.ec.europa.eu",
        "weight": "primary"
      },
      {
        "id": "ONET",
        "version": "29.0",
        "uri": "https://www.onetcenter.org",
        "weight": "secondary"
      },
      {
        "id": "EQF",
        "version": "2008/C111/01",
        "uri": "https://europass.europa.eu/en/description-eight-eqf-levels",
        "weight": "level_scale"
      }
    ],

    "competencies": [
      {
        "id": "ESCO:S/b89e5af8-3f5f-4cf3-b4d0-27de7d76a4d2",
        "label": "waste collection procedures",
        "label_fr": "procédures de collecte des déchets",
        "type": "skill",
        "domain": "occupational",
        "eqf_level": 2,
        "isco_skill_level": 1,
        "status": "mastered",
        "proficiency": {
          "scale": "EQF",
          "value": 2,
          "descriptor": "Basic skills required to carry out simple tasks"
        },
        "evidence": "Completed 6-month on-the-job training, WAMITAB Level 2 certificate",
        "last_assessed": "2025-09",
        "source": "self_reported"
      },
      {
        "id": "HSE:WM-SAFETY-001",
        "label": "manual handling in waste collection",
        "label_fr": "manutention manuelle en collecte de déchets",
        "type": "physical",
        "domain": "safety",
        "eqf_level": 1,
        "status": "mastered",
        "proficiency": {
          "scale": "EQF",
          "value": 1,
          "descriptor": "Basic skills required to carry out simple tasks"
        },
        "evidence": "HSE Manual Handling certificate, annual refresher completed",
        "last_assessed": "2025-06",
        "source": "certified"
      },
      {
        "id": "GreenComp:CC2",
        "label": "systems thinking for waste reduction",
        "label_fr": "pensée systémique pour la réduction des déchets",
        "type": "attitude",
        "domain": "sustainability",
        "eqf_level": 2,
        "status": "in_progress",
        "proficiency": {
          "scale": "EQF",
          "value": 1,
          "descriptor": "Emerging awareness"
        },
        "evidence": null,
        "last_assessed": null,
        "source": "self_reported"
      },
      {
        "id": "DigComp:1.1",
        "label": "browsing and searching digital data",
        "label_fr": "navigation et recherche de données numériques",
        "type": "digital",
        "domain": "information_literacy",
        "eqf_level": 1,
        "status": "in_progress",
        "proficiency": {
          "scale": "DigComp",
          "value": 2,
          "descriptor": "Foundation"
        },
        "evidence": "Uses mobile app for route optimization",
        "last_assessed": "2025-10",
        "source": "self_reported"
      }
    ],

    "skill_gaps": [
      {
        "id": "ESCO:S/hazardous-waste",
        "label": "hazardous waste management",
        "label_fr": "gestion des déchets dangereux",
        "type": "skill",
        "domain": "safety",
        "target_eqf_level": 3,
        "status": "target",
        "priority": "high",
        "recommended_resources": []
      }
    ],

    "meta": {
      "completeness_score": 0.42,
      "frameworks_coverage": ["ESCO", "GreenComp", "DigComp", "HSE"],
      "last_updated": "2025-12-22",
      "agent_session_id": "kai_session_20251222_001"
    }
  }
}
```

### 3.2 Propriétés du schéma

| Propriété | Type | Obligatoire | Description |
|---|---|---|---|
| `occupation.isco_code` | string | **OUI** | Code ISCO-08 — identifiant universel de l'occupation |
| `occupation.esco_uri` | URI | Recommandé | URI ESCO pour l'occupation (si disponible) |
| `occupation.onet_code` | string | Optionnel | Code O*NET-SOC pour le marché américain |
| `occupation.local_framework` | enum | Optionnel | NVQ, NCS, AQF, SkillsFuture, custom |
| `frameworks_referenced` | array | **OUI** | Au moins un framework référencé |
| `competencies[].id` | string | **OUI** | ID namespaced : `FRAMEWORK:ID` |
| `competencies[].type` | enum | **OUI** | knowledge, skill, attitude, physical, safety, civic, digital, language_pro, sustainability |
| `competencies[].eqf_level` | int 1-8 | Recommandé | Niveau EQF de la compétence |
| `competencies[].status` | enum | **OUI** | mastered, in_progress, target |
| `competencies[].proficiency` | object | Recommandé | Échelle + valeur + descripteur |
| `competencies[].evidence` | string | Optionnel | Preuve ou justification |
| `competencies[].source` | enum | Recommandé | self_reported, certified, assessed_by_ai, peer_validated |
| `skill_gaps` | array | Optionnel | Compétences cibles à développer |

### 3.3 Enums et valeurs possibles

```json
{
  "type_values": [
    "knowledge",
    "skill",
    "attitude",
    "physical",
    "safety",
    "civic",
    "digital",
    "language_professional",
    "sustainability"
  ],
  "status_values": ["mastered", "in_progress", "target", "obsolete"],
  "source_values": ["self_reported", "certified", "assessed_by_ai", "peer_validated", "employer_validated"],
  "proficiency_scales": {
    "EQF": {"min": 1, "max": 8},
    "DigComp": {"min": 1, "max": 8, "labels": ["Foundation", "Foundation+", "Intermediate", "Intermediate+", "Advanced", "Advanced+", "Highly Specialised", "Highly Specialised+"]},
    "NVQ": {"min": 1, "max": 5},
    "NCS": {"min": 1, "max": 8},
    "ISCO_skill_level": {"min": 1, "max": 4},
    "Novice-Expert": {"labels": ["Novice", "Advanced Beginner", "Competent", "Proficient", "Expert"]}
  }
}
```

### 3.4 Alignement avec les ontologies existantes

| Standard | Alignement |
|---|---|
| **schema.org/DefinedTerm** | `competency.id` → `@id`, `competency.label` → `name`, framework → `inDefinedTermSet` |
| **ESCO API** | `occupation.esco_uri` → lien direct vers l'API ESCO REST |
| **ISCO-08** | `occupation.isco_code` → code universel ILO |
| **Europass** | Compatible avec le modèle de données Europass Digital Credentials |
| **Credential Engine** | Compatible avec CTDL (Credential Transparency Description Language) |
| **JSON-LD** | Le champ peut être sérialisé en JSON-LD avec `@context` ESCO |

---

## Section 4 — Cas d'usage concrets par secteur

### 4.1 Éboueur en formation (ISCO 9121)

**Profil :** Agent de collecte des déchets, 6 mois d'expérience, souhaitant évoluer vers chef d'équipe.

```json
{
  "occupational_competencies": {
    "occupation": {
      "isco_code": "9121",
      "isco_label": "Refuse and Recyclable Material Collectors",
      "esco_label": "refuse collector",
      "local_framework": "NVQ",
      "local_code": "NVQ:L2-WM001"
    },
    "competencies": [
      {
        "id": "WAMITAB:L2-WC001",
        "label": "waste collection route management",
        "type": "skill",
        "eqf_level": 2,
        "status": "mastered",
        "evidence": "WAMITAB Level 2 Award in Waste Management"
      },
      {
        "id": "HSE:MH001",
        "label": "safe manual handling techniques",
        "type": "physical",
        "eqf_level": 1,
        "status": "mastered",
        "evidence": "HSE-accredited training certificate"
      },
      {
        "id": "ESCO:S/vehicle-operation",
        "label": "refuse vehicle operation",
        "type": "skill",
        "eqf_level": 2,
        "status": "in_progress",
        "evidence": "Currently training for HGV Category C licence"
      },
      {
        "id": "GreenComp:CA3",
        "label": "individual sustainability initiative",
        "type": "sustainability",
        "eqf_level": 1,
        "status": "in_progress"
      },
      {
        "id": "LifeComp:S2",
        "label": "collaboration and teamwork",
        "type": "attitude",
        "eqf_level": 2,
        "status": "mastered"
      }
    ],
    "skill_gaps": [
      {
        "id": "WAMITAB:L3-WM001",
        "label": "waste management supervision",
        "type": "skill",
        "target_eqf_level": 3,
        "status": "target",
        "priority": "high"
      }
    ]
  }
}
```

**Compétences clés pour ce profil :**
- Physiques : manutention manuelle, conduite de véhicules spéciaux
- Sécurité : risques biologiques, risques trafic, EPI (Équipements de Protection Individuelle)
- Techniques : tri sélectif, gestion de route, identification déchets dangereux
- Durabilité : économie circulaire, réduction à la source
- Comportementales : travail d'équipe, ponctualité, service au public

---

### 4.2 Enseignant débutant (ISCO 2330)

**Profil :** Professeur de collège en première année d'enseignement.

```json
{
  "occupational_competencies": {
    "occupation": {
      "isco_code": "2330",
      "isco_label": "Secondary Education Teachers",
      "esco_label": "secondary school teacher"
    },
    "frameworks_referenced": [
      {"id": "DigCompEdu", "version": "2017"},
      {"id": "UNESCO_ICT_CFT", "version": "3.0"},
      {"id": "EQF", "weight": "level_scale"}
    ],
    "competencies": [
      {
        "id": "DigCompEdu:3.1",
        "label": "teaching with digital technologies",
        "type": "digital",
        "eqf_level": 4,
        "status": "in_progress",
        "proficiency": {"scale": "DigCompEdu", "value": "B1", "descriptor": "Integrator"}
      },
      {
        "id": "UNESCO_ICT_CFT:PED001",
        "label": "learner-centred pedagogy",
        "type": "skill",
        "eqf_level": 5,
        "status": "mastered"
      },
      {
        "id": "DigCompEdu:5.1",
        "label": "accessibility and inclusion",
        "type": "attitude",
        "eqf_level": 4,
        "status": "in_progress"
      },
      {
        "id": "LifeComp:P1",
        "label": "self-regulation under pressure",
        "type": "attitude",
        "eqf_level": 4,
        "status": "in_progress",
        "evidence": "Classe de 30 élèves difficiles à gérer"
      },
      {
        "id": "ESCO:S/classroom-management",
        "label": "classroom management",
        "type": "skill",
        "eqf_level": 4,
        "status": "struggles",
        "evidence": "Difficultés rapportées lors de l'observation de classe"
      }
    ]
  }
}
```

---

### 4.3 Politicien / Élu local (ISCO 1111)

**Profil :** Conseiller municipal nouvellement élu, sans expérience politique préalable.

```json
{
  "occupational_competencies": {
    "occupation": {
      "isco_code": "1111",
      "isco_label": "Legislators",
      "custom_label": "Municipal Councillor"
    },
    "competencies": [
      {
        "id": "EntreComp:IntoAction.PA",
        "label": "political agency and civic mobilization",
        "type": "civic",
        "eqf_level": 5,
        "status": "in_progress"
      },
      {
        "id": "GreenComp:AS1",
        "label": "political agency for sustainability",
        "type": "civic",
        "eqf_level": 4,
        "status": "target"
      },
      {
        "id": "ESCO:S/public-speaking",
        "label": "public speaking and presentation",
        "type": "skill",
        "eqf_level": 5,
        "status": "mastered"
      },
      {
        "id": "ESCO:S/legislation",
        "label": "legislation drafting and analysis",
        "type": "knowledge",
        "eqf_level": 5,
        "status": "in_progress",
        "evidence": "Suivi formation droit public local (40h)"
      },
      {
        "id": "LifeComp:S1",
        "label": "empathy and perspective-taking",
        "type": "attitude",
        "eqf_level": 5,
        "status": "mastered"
      },
      {
        "id": "EntreComp:Resources.ME",
        "label": "mobilising and managing public resources",
        "type": "skill",
        "eqf_level": 4,
        "status": "struggles",
        "evidence": "Difficultés à lire les budgets municipaux"
      }
    ]
  }
}
```

---

### 4.4 Chirurgien (ISCO 2212)

**Profil :** Chirurgien orthopédique avec 5 ans de spécialisation.

```json
{
  "occupational_competencies": {
    "occupation": {
      "isco_code": "2212",
      "isco_label": "Specialist Medical Practitioners",
      "esco_label": "orthopaedic surgeon",
      "onet_code": "29-1067.00"
    },
    "competencies": [
      {
        "id": "ICN:CareProvision.Implementation",
        "label": "surgical procedure execution",
        "type": "physical",
        "eqf_level": 7,
        "status": "mastered",
        "proficiency": {"scale": "EQF", "value": 7},
        "evidence": "500+ arthroscopies réalisées, board certification"
      },
      {
        "id": "ESCO:S/sterile-technique",
        "label": "maintaining sterile field",
        "type": "safety",
        "eqf_level": 6,
        "status": "mastered"
      },
      {
        "id": "LifeComp:P1",
        "label": "stress management under critical conditions",
        "type": "attitude",
        "eqf_level": 7,
        "status": "mastered"
      },
      {
        "id": "ICN:CareProvision.Teamwork",
        "label": "multi-disciplinary team coordination",
        "type": "attitude",
        "eqf_level": 7,
        "status": "mastered"
      },
      {
        "id": "ONET:29-1067.ROBOTICS",
        "label": "robotic-assisted surgery",
        "type": "skill",
        "eqf_level": 7,
        "status": "in_progress",
        "evidence": "Formation Da Vinci System en cours (12h)"
      }
    ]
  }
}
```

---

### 4.5 Data Scientist (ISCO 2120)

**Profil :** Data Scientist avec 2 ans d'expérience en ML.

```json
{
  "occupational_competencies": {
    "occupation": {
      "isco_code": "2120",
      "isco_label": "Mathematicians, Actuaries and Statisticians",
      "esco_label": "data scientist",
      "onet_code": "15-2051.00"
    },
    "competencies": [
      {
        "id": "ESCO:S/machine-learning",
        "label": "machine learning",
        "type": "skill",
        "eqf_level": 6,
        "status": "mastered",
        "evidence": "3 ML projects in production, Kaggle Expert"
      },
      {
        "id": "ONET:15-2051.PYTHON",
        "label": "Python programming",
        "type": "skill",
        "eqf_level": 6,
        "status": "mastered",
        "evidence": "5+ years daily use, scikit-learn, PyTorch"
      },
      {
        "id": "ESCO:S/data-visualization",
        "label": "data visualization and storytelling",
        "type": "skill",
        "eqf_level": 5,
        "status": "in_progress",
        "evidence": "Difficultés à adapter les visualisations pour audiences non-techniques"
      },
      {
        "id": "NACE:COMM",
        "label": "communicating results to non-technical audiences",
        "type": "attitude",
        "eqf_level": 5,
        "status": "struggles"
      },
      {
        "id": "EntreComp:Ideas.ET",
        "label": "ethical thinking in AI/data",
        "type": "civic",
        "eqf_level": 6,
        "status": "in_progress"
      }
    ]
  }
}
```

---

### 4.6 Artisan charpentier (ISCO 7115)

**Profil :** Charpentier avec 3 ans d'expérience, préparant le NVQ Level 3.

```json
{
  "occupational_competencies": {
    "occupation": {
      "isco_code": "7115",
      "isco_label": "Carpenters and Joiners",
      "esco_label": "carpenter",
      "local_framework": "NVQ",
      "local_code": "NVQ:L3-CARP001"
    },
    "competencies": [
      {
        "id": "NVQ:L2-CARP-FRAME",
        "label": "timber frame construction",
        "type": "skill",
        "eqf_level": 3,
        "status": "mastered",
        "evidence": "NVQ Level 2 Carpentry completed, CSCS Blue Card"
      },
      {
        "id": "ESCO:S/technical-drawing",
        "label": "reading and interpreting construction plans",
        "type": "knowledge",
        "eqf_level": 3,
        "status": "mastered"
      },
      {
        "id": "HSE:CONST-001",
        "label": "construction site safety (CSCS)",
        "type": "safety",
        "eqf_level": 2,
        "status": "mastered",
        "evidence": "CSCS Card active"
      },
      {
        "id": "NVQ:L3-CARP-ROOF",
        "label": "complex roofing and advanced joinery",
        "type": "skill",
        "eqf_level": 4,
        "status": "in_progress",
        "evidence": "En cours d'apprentissage NVQ Level 3"
      },
      {
        "id": "NVQ:L3-CARP-SUPERVISION",
        "label": "supervising work activities on site",
        "type": "skill",
        "eqf_level": 4,
        "status": "target",
        "priority": "high"
      }
    ]
  }
}
```

---

## Section 5 — Roadmap d'intégration dans klickdskill

### 5.1 Priorités d'intégration v3.3

| Priorité | Référentiel | Raison | Disponibilité API | Effort |
|---|---|---|---|---|
| 🔴 **P0 — Immédiat** | **ISCO-08** | Identifiant universel d'occupation — backbone obligatoire | OUI (ILOSTAT API) | Faible |
| 🔴 **P0 — Immédiat** | **ESCO v1.2.1** | ~13 939 skills, API REST JSON-LD, 28 langues, libre | OUI (ESCO API) | Moyen |
| 🔴 **P0 — Immédiat** | **EQF 1-8** | Échelle de niveau universelle, déjà partiellement intégrée | Via ESCO | Faible |
| 🟠 **P1 — Court terme** | **O*NET 29.0** | Référence US dominante, API REST complète | OUI (O*NET Web Services) | Moyen |
| 🟠 **P1 — Court terme** | **DigComp 3.0** | Compétences numériques universelles, 8 niveaux | Partiel (via ESCO) | Faible |
| 🟠 **P1 — Court terme** | **LifeComp** | Soft skills universels — applicable à tout poste | Non (PDF) → à mapper | Moyen |
| 🟡 **P2 — Moyen terme** | **GreenComp** | 12 compétences durabilité, croissance forte dans tous secteurs | Non (PDF) → à mapper | Moyen |
| 🟡 **P2 — Moyen terme** | **EntreComp** | 15 compétences entrepreneuriales, 8 niveaux | Non (PDF) → à mapper | Moyen |
| 🟡 **P2 — Moyen terme** | **NCS (Corée)** | 880 unit groups, aligned EQF, marché coréen | Partiel | Élevé |
| 🟡 **P2 — Moyen terme** | **AQF + Training.gov.au** | API publique, Pacifique + Commonwealth | OUI (Training.gov.au API) | Moyen |
| 🟢 **P3 — Long terme** | **NVQ UK** | Ofqual Register API, cols bleus UK | OUI (Ofqual API) | Moyen |
| 🟢 **P3 — Long terme** | **SkillsFuture SG** | Singapour — pas d'API publique | Non | Élevé |
| 🟢 **P3 — Long terme** | **China NOS** | Données fragmentées, barrière linguistique | Non | Très élevé |
| 🟢 **P3 — Long terme** | **Japan METI DX** | PDF gouvernemental, pas d'API | Non | Élevé |
| 🔵 **P4 — Recherche** | **ICN nursing framework** | Pas de format structuré/API | Non → à mapper | Élevé |
| 🔵 **P4 — Recherche** | **FAO/CABI Agriculture** | Pas de format structuré | Non → à mapper | Élevé |

### 5.2 Référentiels disponibles en API/JSON — Récapitulatif

| Référentiel | API type | Format | Gratuit | URL API |
|---|---|---|---|---|
| **ESCO v1.2.1** | REST | JSON-LD, CSV, RDF | ✅ OUI | `https://ec.europa.eu/esco/api/` |
| **O*NET** | REST | JSON/XML | ✅ OUI | `https://services.onetcenter.org/ws/` |
| **ILOSTAT (ISCO)** | REST | JSON, CSV | ✅ OUI | `https://ilostat.ilo.org/resources/` |
| **UNESCO UIS** | REST | JSON | ✅ OUI | `http://data.uis.unesco.org/` |
| **Training.gov.au (AQF)** | REST | JSON | ✅ OUI | `https://training.gov.au/api/` |
| **OECD iLibrary** | REST | JSON | Partiel | `https://stats.oecd.org/SDMX-JSON/` |
| **Europass** | REST | JSON-LD | ✅ OUI | `https://api.europass.eu/` |

### 5.3 Plan d'implémentation technique

#### Phase 1 — v3.3 (Q1 2026) : Fondation ISCO + ESCO
```
1. Intégrer le crosswalk ISCO-08 → ESCO URI dans le générateur .klickd
2. Implémenter l'occupation auto-detection via O*NET keyword search API
3. Mapper les 4 types de compétences ESCO (knowledge, language, skill, transversal)
4. Ajouter l'échelle EQF 1-8 comme champ de proficiency universel
5. Ajouter les types manquants : physical, safety, civic, sustainability
```

#### Phase 2 — v3.4 (Q2-Q3 2026) : Soft skills et durabilité
```
1. Mapper LifeComp (9 compétences) en JSON statique intégré
2. Mapper GreenComp (12 compétences) en JSON statique
3. Mapper EntreComp (15 compétences, 8 niveaux)
4. Intégrer DigComp 3.0 niveaux 1-8 comme sous-type des compétences digitales
5. Connecter DigCompEdu pour les profils enseignants
```

#### Phase 3 — v3.5 (Q4 2026) : Marchés régionaux
```
1. Intégrer O*NET Web Services pour le marché américain
2. Intégrer Training.gov.au API pour l'Australie
3. Mapper NVQ 1-5 pour le marché UK (via Ofqual API)
4. Connecter UNESCO UIS ISCED pour le contexte éducatif global
```

### 5.4 Estimation des efforts

| Tâche | Effort estimé | Compétences requises |
|---|---|---|
| Schéma JSON `occupational_competencies` | 3 jours | JSON Schema, TypeScript |
| Intégration ESCO API (occupation + skills) | 5 jours | REST API, JSON-LD parsing |
| Crosswalk ISCO ↔ ESCO ↔ O*NET | 3 jours | Data mapping, CSV processing |
| Mappage statique LifeComp/GreenComp/EntreComp | 4 jours | Data curation manuelle |
| UI dans l'app Kai pour saisie compétences | 7 jours | React/TypeScript, UX |
| Logique d'inférence (AI suggère des skills) | 10 jours | Prompt engineering, LLM |
| Tests et validation cross-secteurs | 5 jours | QA, validation métier |
| **TOTAL Phase 1** | **~37 jours** | Équipe 2-3 personnes |

---

## Annexe — Références complètes

| Référentiel | URL officielle |
|---|---|
| ESCO v1.2.1 | https://esco.ec.europa.eu |
| EQF Niveaux | https://europass.europa.eu/en/description-eight-eqf-levels |
| DigComp 3.0 | https://joint-research-centre.ec.europa.eu/digcomp_en |
| DigCompEdu | https://joint-research-centre.ec.europa.eu/digcompedu_en |
| EntreComp | https://joint-research-centre.ec.europa.eu/entrecomp-entrepreneurship-competence-framework_en |
| LifeComp | https://joint-research-centre.ec.europa.eu/lifecomp_en |
| GreenComp | https://joint-research-centre.ec.europa.eu/greencomp-european-sustainability-competence-framework_en |
| O*NET Online | https://www.onetonline.org |
| O*NET Resource Center | https://www.onetcenter.org |
| O*NET Web Services | https://services.onetcenter.org |
| DOL Competency Models | https://www.careeronestop.org/CompetencyModel/ |
| NACE Career Readiness (2024) | https://www.naceweb.org/career-readiness/competencies/career-readiness-defined/ |
| NACE PDF 2024 | https://www.naceweb.org/docs/default-source/default-document-library/2024/resources/nace-career-readiness-competencies-revised-apr-2024.pdf |
| SCANS | https://wdr.doleta.gov/SCANS/ |
| NCS Korea | https://www.ncs.go.kr / https://www.hrdkorea.or.kr/ENG/8/1 |
| SkillsFuture Singapore | https://www.skillsfuture.gov.sg/skills-framework |
| AQF Australia | https://www.aqf.edu.au |
| Training.gov.au | https://training.gov.au |
| MOHRSS China | http://www.mohrss.gov.cn |
| METI Japan DX Skills | https://www.meti.go.jp/english/ |
| ISCO-08 (ILO) | https://ilostat.ilo.org/methods/concepts-and-definitions/classification-occupation/ |
| ISCO-08 Full classification | https://isco-ilo.netlify.app/en/isco-08/ |
| UNESCO ISCED | http://uis.unesco.org/en/topic/international-standard-classification-education-isced |
| OECD Skills 2030 | https://www.oecd.org/en/about/projects/future-of-education-and-skills-2030.html |
| OECD Skills Outlook 2025 | https://worlddidac.org/news/oecd-skills-outlook-2025-building-the-skills-of-the-21st-century-for-all/ |
| ITU Digital Skills Guidebook | https://academy.itu.int/research-advocacy-and-convening-platforms/research-publications/digital-skills-assessment-guidebook |
| ICN Nursing Framework | https://www.icn.ch |
| ICN Nursing Continuum PDF | https://www.commonwealthnurses.org/ARC/Documents/Resources/ICN%20Nursing%20care%20continuum.pdf |
| WHO Competency Framework | https://www.icn.ch/news/international-council-nurses-welcomes-whos-new-competency-framework-world-health-worker-week |
| UNESCO ICT CFT Teachers | https://www.unesco.org/en/articles/ai-competency-framework-teachers |
| UNESCO DigComp Teachers | https://connect.unevoc.unesco.org/home/Digital+Competence+Frameworks |
| NVQ UK Wikipedia | https://en.wikipedia.org/wiki/National_Vocational_Qualification |
| NVQ Level 3 Carpentry | https://www.csttraining.co.uk/what-is-a-level-3-nvq-in-carpentry/ |
| CABI Agriculture Skills | https://www.cabi.org/products-and-services/academy/skills-framework/ |
| HSE Waste Collection | https://www.hse.gov.uk/waste/collection.htm |
| WAMITAB | https://www.wamitab.org.uk |
| klickd.app | https://klickd.app |

---

*Document produit pour Luxlearn.app / klickd.app — Décembre 2025*  
*Ce document constitue la base de spécification pour l'implémentation du champ `occupational_competencies` dans le format .klickd v3.3.*
