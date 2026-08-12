# Note d'architecture - Monitoring et fallback LLM

## Contexte

La plateforme MLOps expose plusieurs fonctionnalités : prédiction Machine Learning classique, RAG documentaire, extraction structurée et classification zero-shot. Les embeddings et la recherche vectorielle restent locaux via sentence-transformers et FAISS. La génération de texte est assurée par Groq afin d'obtenir une latence exploitable en développement et en démonstration.

Ce choix introduit une dépendance externe : indisponibilité réseau, quota dépassé ou erreur API. La plateforme doit donc rester observable et dégrader son comportement proprement.

## Monitoring

L'API expose `/metrics` au format Prometheus. Deux familles de métriques sont utilisées :

- métriques HTTP automatiques via `prometheus-fastapi-instrumentator` ;
- métriques métier IA définies dans `src/monitoring.py`.

Les métriques métier principales sont :

| Métrique | Objectif |
|---|---|
| `mlops_llm_requests_total` | suivre les appels IA par endpoint et statut |
| `mlops_llm_fallbacks_total` | mesurer les erreurs LLM ayant déclenché une réponse dégradée |
| `mlops_llm_request_duration_seconds` | observer la latence des endpoints IA |
| `mlops_rag_retrieved_documents` | suivre l'activité de récupération FAISS |

Prometheus collecte ces métriques toutes les 10 secondes. Grafana est provisionné automatiquement avec une datasource Prometheus et un dashboard initial.

## Fallback Groq

Le fallback vise à préserver la stabilité de l'API même si Groq devient indisponible.

Pour `/ask`, la recherche FAISS locale reste exécutée. Si la génération Groq échoue, l'API retourne les sources locales les plus pertinentes ainsi qu'un message explicite. Le champ `fallback` vaut alors `true`.

Pour `/extract`, l'API retourne toujours une structure JSON stable avec les champs attendus. En cas d'erreur LLM, les valeurs sont nulles et `fallback` vaut `true`.

Pour `/classify`, l'API retourne `Erreur_Classification` en cas d'erreur LLM et expose également `fallback: true`.

Cette stratégie évite les ruptures côté client, facilite la démonstration et rend les incidents visibles dans Prometheus/Grafana.

## Démonstration

La stack locale se lance avec :

```powershell
make monitoring-up
```

Puis le trafic de démonstration peut être généré avec :

```powershell
make demo-traffic
```

Les résultats sont observables dans Grafana sur `http://127.0.0.1:3000`.
