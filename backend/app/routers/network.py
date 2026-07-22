from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app import models, auth

router = APIRouter(prefix="/api/network", tags=["network"])


@router.get("/graph")
def get_graph(
    district: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Build a node/edge graph:
      - case nodes
      - person nodes
      - case -> person edges ("linked_to")
      - person -> person edges when they share a phone number across different
        cases (a recurring-suspect signal worth an investigator's attention)
    """
    query = db.query(models.Case).options(joinedload(models.Case.persons))
    if district:
        query = query.filter(models.Case.district == district)
    cases = query.all()

    nodes = []
    edges = []
    phone_to_persons = defaultdict(list)

    for case in cases:
        nodes.append({
            "id": f"case:{case.id}",
            "type": "case",
            "label": case.case_id,
            "sublabel": case.title,
            "severity": case.severity.value,
            "district": case.district,
            "ref_id": case.id,
        })
        for person in case.persons:
            person_node_id = f"person:{person.id}"
            nodes.append({
                "id": person_node_id,
                "type": "person",
                "label": person.name,
                "sublabel": person.role_in_case or "unknown role",
                "phone": person.phone_number,
                "ref_id": person.case_id,
            })
            edges.append({
                "source": person_node_id,
                "target": f"case:{case.id}",
                "kind": "linked_to",
            })
            if person.phone_number:
                phone_to_persons[person.phone_number].append(person)

    # Recurring-suspect edges: same phone number appearing across different cases
    recurring_count = 0
    for phone, persons in phone_to_persons.items():
        distinct_cases = {p.case_id for p in persons}
        if len(distinct_cases) > 1 and len(persons) > 1:
            for i in range(len(persons)):
                for j in range(i + 1, len(persons)):
                    edges.append({
                        "source": f"person:{persons[i].id}",
                        "target": f"person:{persons[j].id}",
                        "kind": "shared_phone",
                    })
                    recurring_count += 1

    return {"nodes": nodes, "edges": edges, "recurring_links": recurring_count}
