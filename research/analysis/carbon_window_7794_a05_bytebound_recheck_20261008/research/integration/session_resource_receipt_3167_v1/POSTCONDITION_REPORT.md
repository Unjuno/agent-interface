# Receipt binding and postcondition separation

Issue: #3167.

Fresh Docker/Xvfb :154 with two real GTK fixtures and valid session/resource-bound receipts.

- useful: receipt bound, transport completed, 4 emissions, independent effect present, SUCCESS
- no_effect: receipt bound, transport completed, 4 emissions, no independent effect, ACCEPTED_NO_EFFECT

Decision: PASS_TRANSPORT_POSTCONDITION_SEPARATION_SCOPED.

This demonstrates that receipt validity and transport completion do not imply application task success. No model or network calls; one GTK/X11 topology only.
