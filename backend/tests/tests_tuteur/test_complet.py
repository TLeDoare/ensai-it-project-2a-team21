import json
import os
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import classification_report, confusion_matrix

# Importer votre service de traitement complet (à adapter selon votre structure exacte)
from business_object.person import Person
from service.doc_service import DocService


def load_ground_truth(json_path: str) -> Dict[str, List[Dict[str, Any]]]:
    """Charge le fichier JSON contenant la vérité terrain des PII."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {el["doc_id"]: el["spans"] for el in data}


def overlap(span1: Tuple[int, int], span2: Tuple[int, int]) -> bool:
    """Vérifie si deux intervalles (start, end) se chevauchent."""
    start1, end1 = span1
    start2, end2 = span2
    return max(start1, start2) < min(end1, end2)


def evaluate_predictions(
    predicted_spans: List[Dict[str, Any]], 
    gt_spans: List[Dict[str, Any]],
    strict_position: bool = False
) -> Dict[str, Any]:
    """
    Compare les prédictions du pipeline avec la vérité terrain pour un document.
    Retourne la liste des TP, FP, FN pour la matrice de confusion.
    """
    y_true = []
    y_pred = []
    
    matched_gt = set()
    
    for pred in predicted_spans:
        pred_type = str(pred.get("type", "UNKNOWN")).upper()
        pred_start = pred.get("start", -1)
        pred_end = pred.get("end", -1)
        
        match_found = False
        for idx, gt in enumerate(gt_spans):
            if idx in matched_gt:
                continue
                
            gt_type = str(gt.get("type", "UNKNOWN")).upper()
            gt_start = gt.get("start", -1)
            gt_end = gt.get("end", -1)
            
            # Vérification du type
            if pred_type == gt_type:
                # Vérification de la position (recouvrement ou égalité stricte)
                pos_match = (pred_start == gt_start and pred_end == gt_end) if strict_position else overlap((pred_start, pred_end), (gt_start, gt_end))
                
                if pos_match:
                    y_true.append(gt_type)
                    y_pred.append(pred_type)
                    matched_gt.add(idx)
                    match_found = True
                    break
        
        # PII détectée mais absente/incohérente -> Faux Positif (prédit PII, était Hors-PII/Autre)
        if not match_found:
            y_true.append("NO_PII")
            y_pred.append(pred_type)
            
    # PII attendues mais non détectées -> Faux Négatifs
    for idx, gt in enumerate(gt_spans):
        if idx not in matched_gt:
            gt_type = str(gt.get("type", "UNKNOWN")).upper()
            y_true.append(gt_type)
            y_pred.append("NO_PII")
            
    return {"y_true": y_true, "y_pred": y_pred}


def test_evaluer_pipeline_pii():
    """Test global d'évaluation du pipeline et affichage de la matrice de confusion."""
    base_dir = os.path.dirname(__file__)
    docs_dir = os.path.join(base_dir, "documents_test")
    gt_path = os.path.join(base_dir, "ground_truth_spans.json")
    
    # 1. Chargement de la Vérité Terrain
    assert os.path.exists(gt_path), f"Fichier non trouvé : {gt_path}"
    ground_truth = load_ground_truth(gt_path)
    
    all_y_true = []
    all_y_pred = []
    
    doc_service = DocService() # Instanciez votre service de pipeline ici

    print("\n--- Début du test du pipeline complet ---")
    import asyncio

    from business_object.analyser.analyser_factory import AnalyserFactory
    from business_object.types import PII, AnalysisFail

    conversion_pii = {
        PII.last_name: "PERSON",
        PII.first_name: "PERSON",
        PII.birthdate: "DATE_OF_BIRTH",
        PII.NIR: "NIR",
        PII.IBAN: "IBAN",
        PII.email: "EMAIL",
        PII.phone_number: "PHONE",
        PII.CNI: "INTERNAL_ID",
        PII.EX_CNI: "INTERNAL_ID",
        PII.PAN: "IBAN",
        PII.postal_code: "LOCATION",
        PII.immatriculation: "LICENSE_PLATE",
        PII.IP_V4: "LOCATION",
        PII.IP_V6: "LOCATION",
        PII.SIREN: "ORG",
        PII.cadastre: "LOCATION",
        PII.GPS: "LOCATION",
        PII.place: "LOCATION",
        PII.organism: "ORG",
        PII.job: "JOB_TITLE",
        PII.family_relationships: "RELATIVE",
        PII.private_life: "PERSON",
        PII.judiciary_situation: "PERSON",
        PII.income: "PERSON",
        PII.medical: "PERSON",
        PII.ethnicity: "PERSON",
        PII.gender: "PERSON",
        PII.address: "ADDRESS_FULL",
        PII.name: "PERSON"
    }

    
    for filename, gt_spans in ground_truth.items():
        doc_file_path = os.path.join(docs_dir, filename)
        
        if not os.path.exists(doc_file_path):
            print(f"Attention: Le document {filename} n'existe pas dans {docs_dir}")
            continue
            
        with open(doc_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # 2. Exécution du pipeline complet sur le contenu
        # Remplacez cette simulation par votre véritable fonction d'analyse :
        analyser = AnalyserFactory().get_analyser({})
        predicted_spans = asyncio.run(analyser.analyse(content))
        predicted_spans = [{'start': span.indices[0], 'end': span.indices[1], 'type': conversion_pii[span.PII]} for span in list(predicted_spans) if not isinstance(span, AnalysisFail)]
        # predicted_spans = [] # Ex: [{'type': 'NOM', 'start': 12, 'end': 20}]
        
        # 3. Évaluation comparative
        res = evaluate_predictions(predicted_spans, gt_spans, strict_position=False)
        all_y_true.extend(res["y_true"])
        all_y_pred.extend(res["y_pred"])

    # 4. Génération du Rapport et de la Matrice de Confusion
    if not all_y_true:
        pytest.skip("Aucune donnée d'évaluation disponible (exécutez avec vos vraies prédictions).")

    labels = sorted(list(set(all_y_true + all_y_pred)))
    cm = confusion_matrix(all_y_true, all_y_pred, labels=labels)
    
    df_cm = pd.DataFrame(cm, index=[f"Vrai_{l}" for l in labels], columns=[f"Pred_{l}" for l in labels])
    
    print("\n================ MATRICE DE CONFUSION ================")
    print(df_cm)
    print("\n================ RAPPORT DE PERFORMANCE ================")
    print(classification_report(all_y_true, all_y_pred, labels=labels, zero_division=0))

    # Assertion optionnelle : vérifier un seuil minimal de précision/rappel
    # assert accuracy_score(all_y_true, all_y_pred) > 0.70


if __name__ == "__main__":
    # Permet de lancer le fichier directement avec `python test_pipeline_eval.py`
    test_evaluer_pipeline_pii()