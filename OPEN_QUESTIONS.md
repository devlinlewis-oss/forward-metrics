# Open questions

Decisions needed before these definitions can be marked `agreed`. When one is settled,
update the YAML, set `status: agreed`, and delete it from this list.

## Working definitions carried over from the doc ([confirm])

1. **Eligible Submitted Application stage.** Is lifecycle value `845219062` /
   `hs_v2_date_entered_845219062` the right stage and property? (`stages/funnel.yml`)
2. **Old "[to delete]" financial aid statuses.** They're grouped by their notes. Check the
   grouping with Bruno. (`dimensions/fa_status_group.yml`)
3. **Brand vs non-brand search.** Brand = any Google campaign with BRD in its name. PMax
   can also serve brand searches, so non-brand is slightly overstated. Accept as is?
   (`dimensions/google_search_type.yml`)
4. **Tuition fees.** `tuition_fees_personal_area` is free text in mixed formats and isn't
   mapped to degree format. Who owns cleaning it? (`metrics/net_revenue.yml`)

## Gaps found while converting

5. **Definition owners.** Every metric has `owner.definition: unassigned`. Who decides
   what each one means: Celine for spend and benchmarks, admissions for funnel stages,
   Finance for revenue and aid?
6. **"Started Qualified" vs "Activated Application".** The server-side tracking work
   renamed the qualified signal to Activated Application. Should the stage label change,
   and is it still lifecycle value `marketingqualifiedlead`?
7. **Spend per enrolled for one channel.** The doc says "unless a channel is specified".
   When it is, is the denominator that channel's enrolled students (self-reported or
   first visit?) or still everyone enrolled from the market?
8. **Cost per applicant.** The daily cohort report uses Meta + Google spend ÷ applicants
   whose channel is Meta or Google. That isn't in the doc. Add it as its own metric?
   And "applicant" here means submitted, eligible submitted, or started?
9. **Board deck definitions.** The earlier board-deck review found the deck used cost per
   eligible applicant in one place and cost per enrolled in another, and nationality
   rather than High School Country in places. The doc rule is High School Country
   always. Do the board slides move to that rule, or does the board need a nationality
   variant with its own name?
10. **"Applicants" with no qualifier.** People use it to mean started, submitted or
    eligible submitted. Pick a default for the glossary.
11. **Invite rate.** Commonly asked for, not defined. Invited ÷ submitted, or invited ÷
    eligible submitted?

## Deferrals (found in the weekly enrolment analysis, Nov 2026)

12. **Identifying a deferral in HubSpot.** No property or stage is agreed. Candidates on
    contacts: `readmission` (Re-admit Deferred Student), `adm_process_step_deferral_form`
    and `adm_process__step_date__deferral_form` (Deferral form), `defer_start_year`. Which
    one, if any, marks a deferral reliably? (`glossary.yml`, Deferred enrolled)
13. **Backfilling Enrolling for 26/27.** Should the 26/27 Enrolling count be backfilled for
    deferrals who paid before the Nov 2026 process fix and have no Enrolling date?
