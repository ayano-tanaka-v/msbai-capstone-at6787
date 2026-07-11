-- The comparable set: everything in naming_rights_clean except the
-- TARGET row(s) (the Chiba Lotte case, which is never a comparable --
-- it's what we're pricing). TARGET rows stay queryable directly against
-- naming_rights_clean or raw.target_cases.
--
-- This view does not separate OBSERVED from ESTIMATE -- CLAUDE.md
-- section 4 requires keeping estimates out of the *disclosed-only*
-- benchmark, but that segmentation belongs to the analysis-ready step,
-- not here. Filter on row_classification when that distinction matters.

CREATE OR REPLACE VIEW `msbai-capstone-at6787.clean.naming_rights_comparable` AS
SELECT *
FROM `msbai-capstone-at6787.clean.naming_rights_clean`
WHERE row_classification != 'TARGET';
