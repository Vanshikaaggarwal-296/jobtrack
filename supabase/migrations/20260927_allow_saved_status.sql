-- Add the status used for jobs saved from the in-app search.
-- This leaves the existing Supabase table, user data, and RLS policies intact.
DO $$
DECLARE
    status_constraint RECORD;
BEGIN
    FOR status_constraint IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'public.applications'::regclass
          AND contype = 'c'
          AND pg_get_constraintdef(oid) ILIKE '%status%'
    LOOP
        EXECUTE format(
            'ALTER TABLE public.applications DROP CONSTRAINT %I',
            status_constraint.conname
        );
    END LOOP;
END $$;

ALTER TABLE public.applications
    ADD CONSTRAINT applications_status_check
    CHECK (status IN ('Applied', 'Interview', 'Offer', 'Rejected', 'Withdrawn', 'Saved'));
