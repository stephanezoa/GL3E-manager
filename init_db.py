"""
Database initialization script
Loads students and projects data into the database
"""
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.models import Student, Project, AdminUser
from app.utils.security import hash_password
from app.config import settings
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 83 GL3E Students data
STUDENTS_DATA = [
    {"name": "BALEPA LAURENT BRICE", "matricule": "GL.CMR.CMR.D007.2324B"},
    {"name": "BAMOU NTCHAYA PASCAL JUNIOR", "matricule": "GL.CMR.B006.2324"},
    {"name": "DESMUND FREDDY NGANOU NOUWE", "matricule": "GL.CMR.D008.2324A"},
    {"name": "DIVINE FAVOR PRINCE UGO CHUKWU", "matricule": "GL.CMR.Y007.2324I"},
    {"name": "DONGUITSOP GILLES FRANCIS", "matricule": "GL.CMR.Y001.2324R"},
    {"name": "ESSAMA AYI FELIX", "matricule": "GL.CMR.Y016.2324E"},
    {"name": "EYENGA DIVINE KAREL", "matricule": "GL.CMR.G020.2324"},
    {"name": "EYONG MARU-EGBE THERESIA", "matricule": "GL.CMR.D013.2324B"},
    {"name": "FANSI TCHUALIEU JULIEN FREDDY", "matricule": "GL.CMR.M016.2324"},
    {"name": "FOFOU YVES GUSTAVE", "matricule": "GL.CMR.B008.2223A"},
    {"name": "KAMDEM YOUBISSI ANGE GOD GRACE", "matricule": "GL.CMR.Y016.2324H"},
    {"name": "KENMOGNE TCHAMDJOU JOSIAS WILFRIED", "matricule": "GL.CMR.Y024.2324D"},
    {"name": "KIMAYE SANG SARAH OPHENYA", "matricule": "GL.CMR.Y022.2324J"},
    {"name": "KINGNI DJONTU JIRES LEPRINCE", "matricule": "GL.CMR.Y017.2324H"},
    {"name": "KUETE FEUTSOP CARELLE", "matricule": "SR.CMR.Y026.2324A"},
    {"name": "LEMA ESSOMBA BERNADETTE", "matricule": "GL.CMR.Y068.2425G"},
    {"name": "MBESSA SAMBA GISELE LINDA", "matricule": "GL.CMR.MB024.2324"},
    {"name": "MBOUDOU MESSINGA DAMIEN RACHID LOIC", "matricule": "GL.CMR.Y035.2324D"},
    {"name": "MEKONGO MARIE THERESE AUDREY", "matricule": "ATTRIBUTION-PENDING-1"},
    {"name": "MESSINA FOUDA", "matricule": "ATTRIBUTION-PENDING-2"},
    {"name": "MPONGO EKAMBA JOYCELINE ARCELLE", "matricule": "GL.CMR.B042.2324"},
    {"name": "NDOP NISSOUK EUGENE France", "matricule": "GL.CMR.Y3021.2526E"},
    {"name": "NGAZOA ZANGA MAELYS CASSANDRE", "matricule": "GL.CMR.Y045.2324D"},
    {"name": "NGOMNA ETIENNE WILFRIED", "matricule": "GL.CMR.Y1774.2223E"},
    {"name": "NJIOMENI MOUDASSI ERWIN DIMITRI", "matricule": "GL.CMR.D028.2324B"},
    {"name": "NOA ANDRE RUSSEL FREDERIC", "matricule": "GL.CMR.Y050.2324C"},
    {"name": "NWALL A KOUNG ETIENNE PRESTON", "matricule": "GL.CMR.Y050.2324I"},
    {"name": "OBONO JULIENNE DORIANE", "matricule": "GL.CMR.Y052.2324A"},
    {"name": "ONANA EYALA JANE LESLEY", "matricule": "GL.CMR.Y055.2324B"},
    {"name": "ONANA KACK YVES MICHEL", "matricule": "GL.CMR.Y056.2324D"},
    {"name": "ONANA MBOA JOSUE FRANCK YANNICK", "matricule": "GL.CMR.D034.2324B"},
    {"name": "ONANA NGONO APPOLINAIRE STEPHANE", "matricule": "GL.CMR.Y052.2324I"},
    {"name": "OVONO JOSEPH LOIC", "matricule": "GL.CMR.Y056.2324A"},
    {"name": "OVONO NGOMO PAUL MALACHIE", "matricule": "GL.CMR.Y062.2324G"},
    {"name": "PAFO CLAIRE RANELLE", "matricule": "GL.CMR.B0562324"},
    {"name": "PAGNA VICTORIEN EDDY", "matricule": "SR.CMR.B057.2324"},
    {"name": "POUNGUE BOUSSEU JOVIAL CHRIS", "matricule": "GL.CMR.M026.2324B"},
    {"name": "RIM YVES LANDRY", "matricule": "GL.CMR.Y056.2324F"},
    {"name": "RISBETO FEYI DANIEL TRESOR", "matricule": "GL.CMR.G050.2324"},
    {"name": "SAFOU SONFACK EDNEL DUVAL", "matricule": "GL.CMR.D038.2324B"},
    {"name": "SAMBO BEKONDE ABDOULAYE HERMAN", "matricule": "GL.CMR.Y061.2324A"},
    {"name": "SENG MANGAN SUZANNE LESLIE", "matricule": "GL.CMR.D039.2324B"},
    {"name": "SINN SIFA", "matricule": "GL.CMR.Y060.2324F"},
    {"name": "SOH ROMUALD BRICE", "matricule": "GL.CMR.Y056.2324J"},
    {"name": "SONHANA MELI JERRY BOREL", "matricule": "GL.CMR.Y061.2324F"},
    {"name": "SONTIA BEATRICE LEA VICTOIRE", "matricule": "GL.CMR.Y061.2324E"},
    {"name": "TABOU LEONARDI JAUREL", "matricule": "GL.CMR.Y051.2324H"},
    {"name": "TAGNE RAYANE", "matricule": "GL.CMR.Y056.2324I"},
    {"name": "TAGUEFOUET MOMO JINNETTE KARLLY", "matricule": "GL.CMR.Y060.2324D"},
    {"name": "TAKADJIO MOHAMED", "matricule": "GL.CMR.Y014.2324K"},
    {"name": "TAKAM FONKOU DARYL YVAN", "matricule": "ATTRIBUTION-PENDING-3"},
    {"name": "TAKOU FOKOU VALDES", "matricule": "GL.CMR.Y015.2324K"},
    {"name": "TAKOUBE WAFFO GILLS FLORIANT", "matricule": "GL.CMR.B062.2324"},
    {"name": "TALA LIALE EYMARD", "matricule": "GL.CMR.D045.2324A"},
    {"name": "TAMANKEU SONGNY YVES-MALCOM", "matricule": "GL.CMR.M020.2324"},
    {"name": "TCHIENGUE YONDJA HUGUES NOEL", "matricule": "GL.CMR.Y018.2324K"},
    {"name": "TCHIKEU DJEUMEN FRANCHESCA LUCRESSE", "matricule": "GL.CMR.Y061.2324D"},
    {"name": "TCHINDA DOUANLA MIGUEL", "matricule": "GL.CMR.B062.2324-B"},
    {"name": "TCHINDA SOB ANICET JUNIOR", "matricule": "GL.CMR.Y059.2324J"},
    {"name": "TCHONANG KAPSEU LEOFFLER", "matricule": "GL.CMR.D044.2324B"},
    {"name": "TEGANG KUEDA FAREL LARRY", "matricule": "GL.CMR.B065.2324"},
    {"name": "TIDO TEUSSE ZEMDEO LYNE LA FLEURE", "matricule": "GL.CMR.Y060.2324J"},
    {"name": "TIEMGNI WENDY FORTUNE", "matricule": "GL.CMR.Y029.2324K"},
    {"name": "TIOTFEU MAWAMBA VARNELLE", "matricule": "GL.CMR.D047.2324B"},
    {"name": "TOTSEU DASSI NATHANAEL", "matricule": "GL.CMR.D048.2324B"},
    {"name": "TOUKAM TAMBO ANGE ERIKA", "matricule": "GL.CMR.B067.2324"},
    {"name": "TOUOSSOK FOSSOK FABRICIA", "matricule": "GL.CMR.D049.2324B"},
    {"name": "TSALA OWONA GUILLAUME SCHAGUY", "matricule": "GL.CMR.Y035.2324K"},
    {"name": "TSANGA NDI ANDY MICHAEL", "matricule": "GL.CMR.Y036.2324K"},
    {"name": "TSOGMO ATEUFO ARTHUR", "matricule": "GL.CMR.Y037.2324K"},
    {"name": "TSOPGNI GOUFACK FORTUNE NIKEL", "matricule": "GL.CMR.Y039.2324K"},
    {"name": "TUENO DJOUMESSI FREDY MAEL", "matricule": "GL.CMR.MB051.2324"},
    {"name": "WADJA WATCHO ADER DIVIN", "matricule": "GL.CMR.Y044.2324K"},
    {"name": "WAFFO FOKAM PRINCE WILFRIED", "matricule": "GL.CMR.Y062.2324J"},
    {"name": "YAKWA NKWENGWA CHERYLE MARCELLE", "matricule": "GL.CMR.D049.2324A"},
    {"name": "YMELE KITIO KEYSSEL", "matricule": "GL.CMR.Y050.2324K"},
    {"name": "YOUGO ELSA DANIELLE", "matricule": "GL.CMR.Y052.2324K"},
    {"name": "ZOA ONDOBO PAUL STEPHANIE", "matricule": "GL.CMR.Y060.2122G"},
    {"name": "ZONGO BRIGITTE NICAISE", "matricule": "GL.CMR.Y065.2324G"},
    {"name": "ASSE SALOMON YANNICK", "matricule": "GL.CMR.Y003.2324H"},
    {"name": "NGA AVELE HUGUES FELICIEN", "matricule": "GL.CMR.Y034.2324H"},
    {"name": "COULIBALY KALILOU", "matricule": "GL.CMR.D009.2324B"},
    {"name": "TANEDJEU DONFACK SATHURIN GEORDAN", "matricule": "GL.CMR.Y054.2324H"},
]


# 70 Java EE Projects data
PROJECTS_DATA = [
    {"title": "Système de gestion d'étudiants", "description": "Authentification / inscription, Gestion des profils étudiants, Saisie et consultation des notes par matière, Gestion des absences et justificatifs, Génération de bulletins / relevés de notes, Recherche par nom, matricule, classe"},
    {"title": "Gestion de bibliothèque", "description": "Gestion des livres, Gestion des adhérents / utilisateurs, Emprunt et retour de livres, Historique des emprunts par utilisateur, Recherche avancée, Alerte pour retards"},
    {"title": "To-Do List collaborative", "description": "Création de listes de tâches, Attribution de tâches, États des tâches, Commentaires, Priorités et dates d'échéance, Filtre par utilisateur / statut, Blog personnel avec administration"},
    {"title": "Gestion des articles (CRUD)", "description": "Catégories et tags, Système de commentaires (avec modération), Authentification admin / visiteurs, Recherche par mot-clé / catégorie, Compteur de vues"},
    {"title": "Gestion des employés", "description": "Fiches employés, Demande et validation de congés, Suivi des présences, Historique des affectations, Recherche par département / nom"},
    {"title": "Plateforme de quiz en ligne", "description": "Création de quiz par un enseignant, Ajout de questions (QCM, texte, vrai/faux), Passage du quiz par les étudiants, Calcul automatique du score, Historique des résultats, Classement général"},
    {"title": "Gestion d'événements", "description": "Création et modification d'événements, Inscription des participants, Calendrier / agenda, Gestion des places disponibles, Confirmation par email (simulation), Liste des inscrits"},
    {"title": "Réservation de salles", "description": "Liste des salles disponibles, Planning / calendrier des réservations, Formulaire de réservation, Vérification des conflits horaires, Historique des réservations, Annulation"},
    {"title": "Suivi des dépenses personnelles", "description": "Ajout de dépenses et revenus, Catégories (alimentation, transport, loisirs…), Visualisation mensuelle / annuelle, Bilan par catégorie, Graphiques simples"},
    {"title": "Gestion de stock simple", "description": "Produits, Entrées et sorties de stock, Seuil d'alerte de rupture, Historique des mouvements, Recherche par référence / nom"},
    {"title": "Carnet d'adresses / Annuaire", "description": "Gestion des contacts, Groupes / catégories, Recherche avancée, Export CSV, Notes personnelles"},
    {"title": "Prise de rendez-vous médicaux", "description": "Gestion des patients, Planning des médecins / créneaux, Prise de rendez-vous, Historique des consultations, Annulation / report"},
    {"title": "Sondages en ligne", "description": "Création de sondages, Vote anonyme ou identifié, Résultats en temps réel, Partage du lien du sondage, Export des résultats"},
    {"title": "Gestion d'un club sportif", "description": "Gestion des membres, Calendrier des matchs et entraînements, Saisie des scores / résultats, Classement de l'équipe, Cotisations et paiements, Suivi de progression sportive"},
    {"title": "Gestion de parking", "description": "Gestion des places (libres / occupées), Entrée / sortie des véhicules, Calcul du temps passé / tarif, Historique par plaque, Recherche par immatriculation"},
    {"title": "Location de véhicules", "description": "Catalogue des véhicules, Réservation avec dates, Vérification des disponibilités, Calcul du prix, État du véhicule (avant/après)"},
    {"title": "Gestion de recettes culinaires", "description": "Ajout de recettes (ingrédients, étapes), Catégories / difficulté / temps, Favoris, Recherche par ingrédient, Liste de courses"},
    {"title": "Watchlist films / séries", "description": "Ajout de films/séries, Statut (à voir, en cours, terminé), Note personnelle / commentaire, Recherche par genre / année, Recommandations simples"},
    {"title": "Gestion de playlists musicales", "description": "Création de playlists, Ajout / suppression de morceaux, Recherche de titres / artistes, Favoris, Partage de playlist"},
    {"title": "Gestion de budget familial", "description": "Revenus et dépenses mensuels, Catégories budgétaires, Objectifs d'épargne, Alertes dépassement, Bilan mensuel"},
    {"title": "Réservation de tickets cinéma", "description": "Liste des films à l'affiche, Séances et salles, Choix des places, Paiement simulé, Téléchargement du ticket (PDF)"},
    {"title": "Boutique en ligne simple", "description": "Catalogue produits, Ajout au panier, Validation de commande, Espace client (historique), Gestion stock"},
    {"title": "Plateforme de suggestions / feedback", "description": "Soumission d'idées / remarques, Catégorisation, Vote sur les idées, Statut (en cours, traité), Commentaires"},
    {"title": "Gestion de stages", "description": "Publication d'offres de stage, Candidatures, Suivi des candidatures, Validation par l'entreprise, Rapport de stage"},
    {"title": "Gestion d'une petite association", "description": "Membres et cotisations, Événements de l'association, Budget, PV de réunion, Annonces"},
    {"title": "Partage de notes de cours", "description": "Upload de documents / notes, Catégories / matières, Commentaires, Recherche par matière, Téléchargement"},
    {"title": "Gestion des devoirs", "description": "Création de devoirs par prof, Soumission par élèves, Notation, Commentaires du prof, Calendrier des rendus"},
    {"title": "Système de vote de classe", "description": "Création de scrutins, Vote anonyme ou identifié, Résultats en temps réel, Historique des votes, Export"},
    {"title": "Suivi de colis (simulation)", "description": "Enregistrement des envois, Statuts (préparé, expédié, livré), Suivi par numéro, Historique, Recherche"},
    {"title": "Gestion hospitalière simplifiée", "description": "Dossier patient, Rendez-vous, Consultations / historique, Gestion des lits / chambres, Ordonnances"},
    {"title": "E-commerce", "description": "Catalogue multi-catégories, Panier d'achat, Gestion des commandes, Espace client, Gestion des stocks"},
    {"title": "Réservation d'hôtel", "description": "Types de chambres, Calendrier des disponibilités, Réservation multi-nuits, Calcul du prix, Annulation"},
    {"title": "Gestion de restaurant", "description": "Menu / plats, Commandes en ligne, Gestion des tables, Facturation, Statistiques journalières"},
    {"title": "Système de gestion scolaire complet", "description": "Élèves / classes / professeurs, Emplois du temps, Notes par période, Bulletins, Absences"},
    {"title": "Plateforme e-learning", "description": "Création de cours, Upload vidéos / documents, Quiz par module, Progression de l'étudiant, Certificat de fin"},
    {"title": "Gestion de bibliothèque universitaire", "description": "Livres + thèses, Réservation de livres, Prêts prolongés, Amendes automatiques, Statistiques d'emprunt"},
    {"title": "Gestion de projet", "description": "Création de projets, Tâches + sous-tâches, Attribution à des membres, États d'avancement, Commentaires"},
    {"title": "Réservation de vols", "description": "Recherche de vols, Choix de siège, Réservation, Historique des voyages, Annulation"},
    {"title": "Covoiturage local", "description": "Publication de trajets, Recherche de trajets, Réservation de place, Notation conducteurs/passagers, Messagerie"},
    {"title": "Gestion de pharmacie", "description": "Gestion des médicaments, Ordonnances, Vente / délivrance, Stock et ruptures, Historique des ventes"},
    {"title": "Gestion de salle de sport", "description": "Abonnements, Planning des cours collectifs, Réservation de créneaux, Suivi des présences, Facturation"},
    {"title": "Banque en ligne", "description": "Comptes courants / épargne, Virements internes et externes, Historique des opérations, Gestion des cartes, Alertes SMS/email"},
    {"title": "Marketplace multi-vendeurs", "description": "Inscription vendeurs, Gestion boutique par vendeur, Catalogue multi-vendeurs, Panier multi-boutiques, Commission plateforme"},
    {"title": "Gestion de chaîne logistique", "description": "Fournisseurs, Commandes fournisseurs, Stocks multi-entrepôts, Livraisons clients, Suivi en temps réel"},
    {"title": "Plateforme freelance", "description": "Profils freelances, Publication de missions, Dépôt de candidatures, Contrats / milestones, Système de notation"},
    {"title": "Gestion RH complète", "description": "Recrutement, Gestion des employés, Paie simulée, Congés / absences, Évaluations annuelles"},
    {"title": "Application de gestion de santé connectée", "description": "Dossier médical patient, Prise de rendez-vous en ligne, Téléchargement d'ordonnances, Rappels de médicaments, Suivi des constantes"},
    {"title": "Système de gestion d'une université complète", "description": "Gestion des étudiants, enseignants, départements, Inscriptions, Emplois du temps, Gestion des notes, Bulletins (PDF)"},
    {"title": "Plateforme de tournois e-sport", "description": "Création et inscription à des tournois, Gestion des équipes et joueurs, Bracket / arbre de tournoi, Saisie des scores, Classement"},
    {"title": "Système de réservation de voyages intégré", "description": "Recherche vols + hôtels + voitures, Réservation multi-étapes, Gestion des itinéraires, Prix dynamiques, Paiement simulé"},
    {"title": "Système de gestion de flotte de livraison", "description": "Gestion des livreurs, Création et attribution de livraisons, Suivi en temps réel des colis, Optimisation d'itinéraires, Facturation"},
    {"title": "Plateforme de crowdfunding local", "description": "Création de campagnes, Système de dons / contreparties, Suivi de la progression, Commentaires, Paiement simulé"},
    {"title": "Système de gestion de coopératives", "description": "Gestion des membres et cotisations, Suivi des productions / stocks, Ventes groupées, Répartition des bénéfices, Rapports financiers"},
    {"title": "Bibliothèque numérique universitaire", "description": "Catalogue de livres numériques et thèses, Réservation / prêt numérique, Recherche avancée, Annotations et favoris, Statistiques"},
    {"title": "Système de vote électronique sécurisé", "description": "Création d'élections / scrutins, Authentification forte, Vote anonyme ou nominatif, Vérification d'intégrité, Dépouillement automatique"},
    {"title": "Plateforme de gestion de formations professionnelles", "description": "Catalogue de formations, Inscription et paiement, Suivi de la présence, Évaluations et certificats, Espace formateur"},
    {"title": "Système de gestion de centres de santé communautaires", "description": "Gestion des patients communautaires, Campagnes de vaccination, Rendez-vous et suivi, Rapports épidémiologiques"},
    {"title": "Application de gestion de marchés locaux", "description": "Inscription des commerçants, Catalogue produits par stand, Commande en ligne / retrait sur place, Paiement à la livraison, Avis"},
    {"title": "Système de gestion de transport scolaire", "description": "Gestion des bus et itinéraires, Inscription des élèves, Suivi des présences, Facturation, Notifications parents"},
    {"title": "Plateforme de gestion de clubs sportifs amateurs", "description": "Inscription membres, Organisation championnats / tournois, Calendrier et résultats, Gestion des cotisations, Statistiques"},
    {"title": "Système intégré de gestion d'une mairie", "description": "Services citoyens, Prise de rendez-vous en ligne, Suivi des demandes / dossiers, Paiement des taxes, Annonces officielles"},
    {"title": "Application de gestion de recyclage / collecte de déchets", "description": "Points de collecte, Inscription des citoyens, Planification des collectes, Suivi des volumes recyclés, Récompenses"},
    {"title": "Système de suivi de projets de fin d'études (PFE)", "description": "Proposition de sujets, Choix et inscription des binômes, Suivi de l'avancement, Soutenances et notations, Archivage"},
    {"title": "Système de gestion de laboratoires universitaires", "description": "Réservation de matériels / salles labo, Gestion des stocks de produits chimiques, Suivi des expériences, Rapports de sécurité"},
    {"title": "Application de gestion de thèses et mémoires", "description": "Dépôt des travaux, Suivi par directeur de thèse, Planning des soutenances, Archivage et recherche, Plagiat check"},
    {"title": "Système de réservation de ressources informatiques", "description": "Réservation de salles PC / logiciels, Planning par salle, Gestion des droits d'accès, Statistiques d'utilisation"},
    {"title": "Plateforme de gestion d'associations étudiantes", "description": "Création et gestion d'assos, Événements et inscriptions, Budget et cotisations, Votes internes, Galerie photos"},
    {"title": "Système de suivi d'activités extracurriculaires", "description": "Inscription aux activités, Suivi des présences, Certificats de participation, Points bonus, Statistiques"},
    {"title": "Application de gestion de bibliothèques départementales", "description": "Catalogue multi-bibliothèques, Prêts inter-bibliothèques, Gestion des usagers, Statistiques, Événements culturels"},
    {"title": "Système intégré de gestion d'une école", "description": "Gestion élèves / classes / profs, Emplois du temps, Notes et absences, Gestion cantine, Facturation, Portail parents"},
]


def init_students(db: Session):
    """Initialize students in database"""
    logger.info("Loading students...")
    count = 0
    for student_data in STUDENTS_DATA:
        existing = db.query(Student).filter(Student.matricule == student_data["matricule"]).first()
        if not existing:
            student = Student(
                full_name=student_data["name"],
                matricule=student_data["matricule"],
                has_project=False
            )
            db.add(student)
            count += 1
    
    db.commit()
    logger.info(f"Loaded {count} students")


def init_projects(db: Session):
    """Initialize projects in database"""
    logger.info("Loading projects...")
    count = 0
    for project_data in PROJECTS_DATA:
        existing = db.query(Project).filter(Project.title == project_data["title"]).first()
        if not existing:
            project = Project(
                title=project_data["title"],
                description=project_data["description"],
                assigned_count=0,
                max_assignments=2  # Can be assigned twice max
            )
            db.add(project)
            count += 1
    
    db.commit()
    logger.info(f"Loaded {count} projects")


def init_admin(db: Session):
    """Initialize admin user"""
    logger.info("Creating admin user...")
    existing = db.query(AdminUser).filter(AdminUser.username == settings.ADMIN_USERNAME).first()
    if not existing:
        admin = AdminUser(
            username=settings.ADMIN_USERNAME,
            password_hash=hash_password(settings.ADMIN_PASSWORD)
        )
        db.add(admin)
        db.commit()
        logger.info(f"Admin user created: {settings.ADMIN_USERNAME}")
    else:
        logger.info("Admin user already exists")


def main():
    """Main initialization function"""
    logger.info("Starting database initialization...")
    
    # Initialize database schema
    init_db()
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Load data
        init_students(db)
        init_projects(db)
        init_admin(db)
        
        logger.info("Database initialization completed successfully!")
        
        # Print summary
        total_students = db.query(Student).count()
        total_projects = db.query(Project).count()
        logger.info(f"Total students: {total_students}")
        logger.info(f"Total projects: {total_projects}")
        
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
