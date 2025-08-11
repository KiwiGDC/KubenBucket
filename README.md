# 🔐 Secure File Transfer

Application web légère permettant de transférer des fichiers en toute sécurité via un lien unique, avec mot de passe optionnel, expiration automatique, et scan antivirus.

---

## ✨ Fonctionnalités

- Upload de fichiers via une interface web moderne
- Protection optionnelle par mot de passe (stocké haché)
- Expiration configurable : 15 min, 1h, 24h, 7 jours
- Lien de téléchargement unique
- **Scan antivirus via ClamAV** à l'upload
- Traitement asynchrone en arrière-plan
- Téléchargement direct depuis **Google Cloud Storage (GCS)**
- Interface utilisateur responsive avec barre de progression

---

## 📦 Prérequis GCP

Ce projet **nécessite un déploiement sur Google Cloud**, via l’un des services suivants :

- [Google Cloud Run](https://cloud.google.com/run)
- [Google Kubernetes Engine (GKE)](https://cloud.google.com/kubernetes-engine) ✅ recommandé

> 🚫 Le stockage local n’est pas supporté. L’application s’appuie sur GCS pour le stockage des fichiers.

---

## ☁️ Infrastructure requise

- 🔐 **Service Account GCP**
- 🪣 **Bucket GCS** pour stocker les fichiers
- 🧪 **Base de données SQL (MySQL ou autre via SQLAlchemy)**

---

## 🔐 Variables d’environnement nécessaires

| Variable | Description |
|---------|-------------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Chemin vers le fichier JSON du service account |
| `GCS_BUCKET_NAME`               | Nom du bucket GCS pour stocker les fichiers |
| `DATABASE_URL`                 | URL de connexion SQLAlchemy à ta base MySQL/PostgreSQL |
| `SERVICE_ACCOUNT_EMAIL`        | Email du Service Account utilisé (pour signer les URLs GCS) |

---

## 🚀 Déploiement avec Helm

Ce projet inclut un chart Helm pour un déploiement simplifié sur Kubernetes (recommandé sur GKE).

### Installation du chart

1.  **Configurez votre contexte `kubectl`** pour qu'il pointe vers votre cluster GKE.
2.  **Installez le chart** depuis le répertoire local :

    ```bash
    helm install my-release ./charts/kubenbucket
    ```

### Personnalisation du déploiement

Vous pouvez surcharger les valeurs par défaut du chart en utilisant l'option `--set` ou en fournissant un fichier de valeurs personnalisé (`-f my-values.yaml`).

#### Exemple : Mettre à jour l'image

Pour déployer une version spécifique de votre application, vous pouvez surcharger les valeurs de l'image :

```bash
helm install my-release ./charts/kubenbucket \
  --set image.repository=gcr.io/my-gcp-project/my-app \
  --set image.tag=v1.2.3
```

#### Exemple : Configurer les variables d'environnement

Les variables d'environnement nécessaires à l'application peuvent être définies dans le chart. Créez un fichier `my-values.yaml` :

```yaml
# my-values.yaml
env:
  GCS_BUCKET_NAME: "votre-nom-de-bucket"
  DATABASE_URL: "mysql+pymysql://user:password@host:port/db"
  SERVICE_ACCOUNT_EMAIL: "votre-email-de-service-account@gcp-project.iam.gserviceaccount.com"
```

Puis installez le chart avec ce fichier :

```bash
helm install my-release ./charts/kubenbucket -f my-values.yaml
```

> **Note :** La variable `GOOGLE_APPLICATION_CREDENTIALS` est généralement gérée via Workload Identity sur GKE et n'a pas besoin d'être définie explicitement dans le chart.

---


## 🔄 Fonctionnement de l'application

- **Upload :**  
  Le fichier est uploadé par le client, envoyé au conteneur (Cloud Run), scanné avec ClamAV, puis stocké dans un bucket GCS si sain.

- **Téléchargement :**  
  Le client accède à un lien signé **GCS directement** (pas via le conteneur), ce qui permet une livraison rapide et sécurisée.

---

## 🔐 Sécurité

- Mot de passe protégé avec `bcrypt`
- Lien à usage unique avec expiration
- Scan antivirus à l’upload
- Téléchargement direct GCS via URL signée
- Aucun fichier conservé en local

