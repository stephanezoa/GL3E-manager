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
    {"name": "MEKONGO MARIE THERESE AUDREY", "matricule": "GL.CMR.Y000.2324A"},
    {"name": "MESSINA FOUDA", "matricule": "GL.CMR.Y000.2324B"},
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
    {"name": "TAKAM FONKOU DARYL YVAN", "matricule": "GL.CMR.Y000.2324C"},
    {"name": "TAKOU FOKOU VALDES", "matricule": "GL.CMR.Y015.2324K"},
    {"name": "TAKOUBE WAFFO GILLS FLORIANT", "matricule": "GL.CMR.B062.2324"},
    {"name": "TALA LIALE EYMARD", "matricule": "GL.CMR.D045.2324A"},
    {"name": "TAMANKEU SONGNY YVES-MALCOM", "matricule": "GL.CMR.M020.2324"},
    {"name": "TCHIENGUE YONDJA HUGUES NOEL", "matricule": "GL.CMR.Y018.2324K"},
    {"name": "TCHIKEU DJEUMEN FRANCHESCA LUCRESSE", "matricule": "GL.CMR.Y061.2324D"},
    {"name": "TCHINDA DOUANLA MIGUEL", "matricule": "GL.CMR.B062.2324"},
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
    {"name": "ZOA ONDOBO PAUL STEPHANE", "matricule": "GL.CMR.Y060.2122G"},
    {"name": "ZONGO BRIGITTE NICAISE", "matricule": "GL.CMR.Y065.2324G"},
    {"name": "ASSE SALOMON YANNICK", "matricule": "GL.CMR.Y003.2324H"},
    {"name": "NGA AVELE HUGUES FELICIEN", "matricule": "GL.CMR.Y034.2324H"},
    {"name": "COULIBALY KALILOU", "matricule": "GL.CMR.D009.2324B"},
    {"name": "TANEDJEU DONFACK SATHURIN GEORDAN", "matricule": "GL.CMR.Y054.2324H"},
]


# 70 Java EE Projects data (abbreviated for brevity - full list will be in final version)
PROJECTS_DATA = [
    {"title": "Système de gestion d'étudiants", "description": "Gestion complète des étudiants avec notes, absences et bulletins"},
    {"title": "Gestion de bibliothèque", "description": "Système de gestion de livres, emprunts et adhérents"},
    {"title": "To-Do List collaborative", "description": "Application de gestion de tâches en équipe"},
    {"title": "Blog personnel avec administration", "description": "Plateforme de blogging avec système de commentaires"},
    {"title": "Gestion des employés", "description": "Système RH pour la gestion du personnel"},
    {"title": "Plateforme de quiz en ligne", "description": "Création et passage de quiz avec scoring automatique"},
    {"title": "Gestion d'événements", "description": "Organisation d'événements avec inscriptions"},
    {"title": "Réservation de salles", "description": "Système de réservation avec gestion des conflits"},
    {"title": "Suivi des dépenses personnelles", "description": "Application de budget personnel avec graphiques"},
    {"title": "Gestion de stock simple", "description": "Inventaire avec alertes de rupture"},
    {"title": "Carnet d'adresses / Annuaire", "description": "Gestion de contacts avec recherche avancée"},
    {"title": "Prise de rendez-vous médicaux", "description": "Planning médical avec gestion des patients"},
    {"title": "Sondages en ligne", "description": "Création et analyse de sondages"},
    {"title": "Gestion d'un club sportif", "description": "Membres, matchs et cotisations"},
    {"title": "Gestion de parking", "description": "Suivi des places et calcul des tarifs"},
    {"title": "Location de véhicules", "description": "Réservation et gestion de flotte"},
    {"title": "Gestion de recettes culinaires", "description": "Partage de recettes avec liste de courses"},
    {"title": "Watchlist films / séries", "description": "Suivi de films et séries à regarder"},
    {"title": "Gestion de playlists musicales", "description": "Création et partage de playlists"},
    {"title": "Gestion de budget familial", "description": "Finances familiales avec objectifs d'épargne"},
    {"title": "Réservation de tickets cinéma", "description": "Choix de séances et places"},
    {"title": "Boutique en ligne simple", "description": "E-commerce basique avec panier"},
    {"title": "Plateforme de suggestions / feedback", "description": "Collecte et vote sur des idées"},
    {"title": "Gestion de stages", "description": "Publication d'offres et candidatures"},
    {"title": "Gestion d'une petite association", "description": "Membres, événements et budget associatif"},
    {"title": "Partage de notes de cours", "description": "Upload et téléchargement de documents"},
    {"title": "Gestion des devoirs", "description": "Soumission et notation de devoirs"},
    {"title": "Système de vote de classe", "description": "Scrutins et résultats en temps réel"},
    {"title": "Suivi de colis (simulation)", "description": "Tracking de livraisons"},
    {"title": "Gestion hospitalière simplifiée", "description": "Dossiers patients et rendez-vous"},
    {"title": "E-commerce", "description": "Boutique en ligne complète"},
    {"title": "Réservation d'hôtel", "description": "Booking de chambres multi-nuits"},
    {"title": "Gestion de restaurant", "description": "Menu, commandes et tables"},
    {"title": "Système de gestion scolaire complet", "description": "École complète avec emplois du temps"},
    {"title": "Plateforme e-learning", "description": "Cours en ligne avec quiz et certificats"},
    {"title": "Gestion de bibliothèque universitaire", "description": "Livres, thèses et amendes"},
    {"title": "Gestion de projet", "description": "Tâches, équipes et suivi d'avancement"},
    {"title": "Réservation de vols", "description": "Recherche et booking de vols"},
    {"title": "Covoiturage local", "description": "Partage de trajets avec notation"},
    {"title": "Gestion de pharmacie", "description": "Médicaments, ordonnances et stock"},
    {"title": "Gestion de salle de sport", "description": "Abonnements et cours collectifs"},
    {"title": "Banque en ligne", "description": "Comptes, virements et historique"},
    {"title": "Marketplace multi-vendeurs", "description": "Plateforme e-commerce multi-boutiques"},
    {"title": "Gestion de chaîne logistique", "description": "Fournisseurs et stocks multi-entrepôts"},
    {"title": "Plateforme freelance", "description": "Missions et contrats freelance"},
    {"title": "Gestion RH complète", "description": "Recrutement, paie et évaluations"},
    {"title": "Application de gestion de santé connectée", "description": "Dossier médical et suivi de santé"},
    {"title": "Système de gestion d'une université complète", "description": "Gestion universitaire intégrée"},
    {"title": "Plateforme de tournois e-sport", "description": "Organisation de compétitions gaming"},
    {"title": "Système de réservation de voyages intégré", "description": "Vols, hôtels et voitures"},
    {"title": "Système de gestion de flotte de livraison", "description": "Livreurs et optimisation d'itinéraires"},
    {"title": "Plateforme de crowdfunding local", "description": "Campagnes de financement participatif"},
    {"title": "Système de gestion de coopératives", "description": "Productions et ventes groupées"},
    {"title": "Bibliothèque numérique universitaire", "description": "Livres numériques et thèses"},
    {"title": "Système de vote électronique sécurisé", "description": "Élections avec vérification d'intégrité"},
    {"title": "Plateforme de gestion de formations professionnelles", "description": "Formations et certifications"},
    {"title": "Système de gestion de centres de santé communautaires", "description": "Santé communautaire et campagnes"},
    {"title": "Application de gestion de marchés locaux", "description": "Commerçants et produits locaux"},
    {"title": "Système de gestion de transport scolaire", "description": "Bus scolaires et itinéraires"},
    {"title": "Plateforme de gestion de clubs sportifs amateurs", "description": "Championnats et statistiques"},
    {"title": "Système intégré de gestion d'une mairie", "description": "Services citoyens et taxes"},
    {"title": "Application de gestion de recyclage / collecte de déchets", "description": "Collecte et points éco-citoyens"},
    {"title": "Système de suivi de projets de fin d'études (PFE)", "description": "Sujets, soutenances et archivage"},
    {"title": "Système de gestion de laboratoires universitaires", "description": "Matériels et produits chimiques"},
    {"title": "Application de gestion de thèses et mémoires", "description": "Dépôt et suivi de thèses"},
    {"title": "Système de réservation de ressources informatiques", "description": "Salles PC et logiciels"},
    {"title": "Plateforme de gestion d'associations étudiantes", "description": "Événements et budget associatif"},
    {"title": "Système de suivi d'activités extracurriculaires", "description": "Activités et certificats"},
    {"title": "Application de gestion de bibliothèques départementales", "description": "Multi-bibliothèques et événements"},
    {"title": "Système intégré de gestion d'une école", "description": "École complète avec cantine et finances"},
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
