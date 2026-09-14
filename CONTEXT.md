# Domain Context

The ubiquitous language for itela's internal CRM. These are the words used in code, in the UI and in conversation. Implementation details do not belong in this file.

## Contact

A person at a client or prospect company. Contacts are the root of the model: every Opportunity belongs to exactly one Contact, and so does every Task.

The company a Contact works for is carried as plain text on the Contact, not as its own entity. itela sells to companies, but at this size a separate Company entity buys nothing the company name does not already give. The ceiling: asking "show me everything for company X" means matching on text.

A Contact is never deleted while it still has Opportunities or Tasks.

## Opportunity

A potential deal with one Contact, valued in USD. An Opportunity carries both a Stage and a Status — they answer different questions and must never be collapsed into one field.

## Stage

Where an Opportunity sits in the sales funnel: **New → Qualified → PoC → Proposal → Negotiation**.

PoC is technical validation — a proof of concept run before quoting, which is a real step when selling technology services.

Stage says nothing about whether a deal is still alive. A closed deal keeps the Stage it had reached, and that is precisely what makes it possible to ask where the funnel leaks.

## Status

Whether an Opportunity is **Open**, **Won** or **Lost**. Always exactly one of the three.

Status is what "closed" means: an Opportunity is closed once its Status is no longer Open, and the moment that happened is recorded. Reports about money in play read Status, never Stage.

## Pipeline

The Opportunities whose Status is Open. Money already Won or Lost is not in the pipeline.

## Task

A piece of work involving a Contact — a call, a meeting, an email, or anything else. A Task always belongs to a Contact, and may additionally belong to one of that Contact's Opportunities.

A Task stays *pending* until it is completed; completing it records when. A Task created from an Opportunity takes its Contact from that Opportunity, so a Task never refers to a Contact unrelated to its own Opportunity.

## Activity history

Not an entity: a Contact's completed Tasks, most recent first. "What has happened with this client?" is answered by reading it.

## Owner

The team member responsible for an Opportunity or a Task, held as a plain name. There is no login yet, so an Owner is a name rather than a reference to a user. Contacts have no Owner.
