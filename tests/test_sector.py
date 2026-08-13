from context_hub.sector import sector_id, can_assert_membership, mapping_use

def test_sector_id():
    assert sector_id(1) == "UAF-SEC-01"
    assert sector_id(55) == "UAF-SEC-55"

def test_acteco_rule_does_not_assert_membership_by_itself():
    row={"mapping_status":"VALIDATED_RULE","legal_membership_assertion_allowed":False}
    assert not can_assert_membership(row, external_validation_satisfied=True)

def test_candidate_is_screening():
    assert mapping_use({"mapping_status":"EMPIRICAL_CANDIDATE"}) == "SCREENING"
