# Assistant Intelligent pour la Gestion de Projets

## Présentation du projet

Ce projet est une plateforme intelligente de gestion de projets développée dans le cadre du Projet de Programmation (PPG) de la formation ING3 à l’École Sesame.

L’objectif est de proposer une alternative moderne aux outils classiques de gestion de projets en intégrant un assistant basé sur l’intelligence artificielle capable d’analyser les tâches, de prédire les retards et de fournir des recommandations personnalisées en temps réel.

---

## Problématique

Comment permettre à une équipe projet de mieux organiser son travail, d’anticiper les blocages et d’améliorer sa productivité grâce à un assistant intelligent intégré à une plateforme de gestion de tâches ?

---

## Objectifs du projet

- Concevoir une application web de gestion de projets avec tableau Kanban interactif (drag & drop)
- Intégrer un assistant IA pour l’analyse et la priorisation des tâches
- Développer une API REST robuste avec Django REST Framework
- Implémenter une interface frontend dynamique en JavaScript vanilla
- Fournir des KPI et des analyses (burn-down chart, statistiques)
- Générer des résumés automatiques hebdomadaires
- Détecter les tâches bloquées et optimiser leur répartition

---

## Acteurs du système

- Administrateur : gestion globale de la plateforme
- Chef de projet : création et supervision des projets
- Membre : exécution et suivi des tâches
- Assistant IA : analyse intelligente et recommandations automatiques

---

## Fonctionnalités principales

### Authentification
- Inscription et connexion sécurisée via JWT
- Gestion des rôles utilisateurs
- Gestion des profils

### Gestion des projets
- Création et suivi des projets
- Invitation de membres
- Tableau de bord de progression

### Kanban interactif
- Système drag & drop des tâches
- Statuts : À faire, En cours, En révision, Terminé
- Sous-tâches et filtres avancés
- Gestion des priorités et deadlines

### Assistant IA
- Chat conversationnel intégré
- Analyse des tâches en temps réel
- Prédiction des retards
- Recommandations personnalisées
- Résumés automatiques des projets

### Analytics
- KPI de performance
- Burn-down chart
- Graphiques statistiques (Chart.js)
- Export des rapports en PDF

### Notifications
- Alertes en temps réel
- Notifications de deadlines
- Résumés hebdomadaires automatiques

---

## Stack technique

### Frontend
- HTML5
- CSS3
- JavaScript

### Backend
- Python
- Django 4.x
- Django REST Framework

### Base de données
- SQLite (développement)
- PostgreSQL (production)

### Intelligence artificielle
- API LLM (Claude Sonnet)

### Outils
- JWT (SimpleJWT)
- Chart.js
- Git / GitHub
- Pytest

---

## Architecture du projet

Le projet suit l’architecture MTV (Model - Template - View) de Django :
- Models : structure des données et ORM
- Views / API : logique métier et endpoints REST
- Frontend : interface utilisateur en JavaScript
- Service IA : traitement intelligent et recommandations
- Analytics : calcul des KPI et visualisations
- Notifications : gestion des alertes et automatisations

---

## Structure du projet

users/ Gestion des utilisateurs et authentification
projects/ Gestion des projets et membres
kanban/ Gestion des tâches et tableau Kanban
ai_assistant/ Module d’intelligence artificielle
analytics/ KPI, statistiques et rapports
notifications/ Système d’alertes et résumés
api/ Endpoints REST et documentation

## Fonctionnalités d’intelligence artificielle

- Priorisation automatique des tâches
- Détection des risques de retard
- Recommandations personnalisées
- Analyse de la charge de travail
- Résumé hebdomadaire automatique
- Détection des tâches bloquées

---

## Objectif final

Développer une plateforme moderne et intelligente permettant aux équipes de mieux organiser leur travail, anticiper les problèmes et améliorer leur productivité grâce à l’intelligence artificielle.

---

## Auteur

Projet réalisé dans le cadre du PPG ING3 – École Sesame

---

## Statut du projet

En cours de développement
