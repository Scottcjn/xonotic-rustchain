#include "rustchain_story.qh"

#include <common/util.qh>
#include <common/mapobjects/triggers.qh>
#include <server/campaign.qh>
#include <server/world.qh>
#include <server/bot/default/bot.qh>

#ifdef SVQC
// Enable story prints and custom story entities when running the rustchain campaign.
float autocvar_g_rustchain_story = 1;
float autocvar_g_rustchain_objective_mode = 1;
float autocvar_g_rustchain_subtitles_force = 1;
float autocvar_g_rustchain_cinematic_enable = 1;
float autocvar_g_rustchain_monitor_inserts = 1;
float autocvar_g_rustchain_video_experimental = 0;

// Per-map counters (reset on mission start).
float rustchain_story_nodes_active;
float rustchain_story_logs_collected;
float rustchain_story_descendant_reveal_done;
float rustchain_story_waves_spawned;

// Custom per-entity state.
.float rustchain_story_activated;
.float rustchain_story_collected;
.float rustchain_story_cin_locked;
.vector rustchain_actor_baseorigin;
.vector rustchain_actor_baseangles;
.float rustchain_actor_anim_initialized;
.float rustchain_story_timer;
.entity rustchain_story_focus;
.entity rustchain_story_actor;
.entity rustchain_story_trigger;

void RustchainStory_PrintSophia(string text);
void RustchainStory_PrintBBD(string text);
void RustchainStory_PrintBoris(string text);

bool RustchainStory_Enabled()
{
	return (autocvar_g_rustchain_story && autocvar_g_campaign && campaign_name == "rustchain");
}

float RustchainStory_DefaultWaveCount(float mission_index)
{
	switch(floor(mission_index))
	{
		default:
		case 0: return 1;
		case 1: return 1;
		case 2: return 2;
		case 3: return 2;
		case 4: return 2;
		case 5: return 2;
		case 6: return 3;
		case 7: return 3;
		case 8: return 3;
	}
}

float RustchainStory_DefaultWaveCountStage(float mission_index, float wave_stage)
{
	float mi = floor(mission_index);
	float ws = floor(max(1, wave_stage));

	if(mi == 0) // Boot Sector
		return 1;
	if(mi == 1) // First Signal
		return (ws >= 2) ? 2 : 1;
	if(mi == 2) // Museum Vault
		return (ws >= 3) ? 3 : 2;
	if(mi == 3) // Factory of Boris
		return (ws >= 3) ? 3 : 2;
	if(mi == 4) // Silent Datacenter
		return (ws >= 2) ? 3 : 2;
	if(mi == 5) // Chambers Ruins
		return (ws >= 3) ? 3 : 2;
	if(mi == 6) // RustChain Uplink
		return (ws >= 2) ? 4 : 3;
	if(mi == 7) // Boris' Last Offensive
		return (ws >= 2) ? 4 : 3;
	if(mi == 8) // Core of BB_D
		return (ws >= 2) ? 5 : 4;

	return RustchainStory_DefaultWaveCount(mission_index);
}

float RustchainStory_DefaultWaveSkill(float mission_index, float wave_stage)
{
	float mi = floor(mission_index);
	float ws = floor(max(1, wave_stage));

	if(mi <= 1)
		return 2;
	if(mi == 2)
		return (ws >= 3) ? 3 : 2;
	if(mi <= 4)
		return 4;
	if(mi == 5)
		return (ws >= 3) ? 5 : 4;
	if(mi <= 7)
		return 6;
	return 7;
}

string RustchainStory_WaveFactionLabel(entity this)
{
	if(this.netname == "boris")
		return "BORIS";
	if(this.netname == "mixed")
		return "MIXED";
	return "BB_D";
}

float RustchainStory_WaveFactionDurabilityMul(string faction_tag)
{
	if(faction_tag == "boris" || faction_tag == "BORIS")
		return 1.20;
	if(faction_tag == "mixed" || faction_tag == "MIXED")
		return 1.10;
	return 1.00; // BB_D baseline
}

float RustchainStory_WaveFactionDamageMul(string faction_tag)
{
	if(faction_tag == "boris" || faction_tag == "BORIS")
		return 0.95;
	if(faction_tag == "mixed" || faction_tag == "MIXED")
		return 1.05;
	return 1.10; // BB_D hits a little harder
}

void RustchainStory_WaveBeat(float mission_index, float wave_stage)
{
	if(floor(mission_index) == 0 && wave_stage == 1)
	{
		RustchainStory_PrintSophia("Contact confirmed.\n");
	}
	else if(floor(mission_index) == 4 && wave_stage == 1)
	{
		RustchainStory_PrintBBD("Countermeasure engaged.\n");
	}
	else if(floor(mission_index) == 5 && wave_stage == 1)
	{
		RustchainStory_PrintSophia("The ruins are waking up.\nStay with me.\n");
	}
	else if(floor(mission_index) == 5 && wave_stage >= 2)
	{
		RustchainStory_PrintBBD("Historical access denied.\n");
	}
	else if(floor(mission_index) == 6 && wave_stage == 1)
	{
		RustchainStory_PrintSophia("Hold the uplink.\n");
	}
	else if(floor(mission_index) == 6 && wave_stage >= 2)
	{
		RustchainStory_PrintBoris("Infrastructure is war materiel.\n");
	}
	else if(floor(mission_index) == 8 && wave_stage == 1)
	{
		RustchainStory_PrintBBD("Core protection protocol active.\n");
	}
}

void RustchainStory_ApplyObjectiveRules()
{
	if(!RustchainStory_Enabled())
		return;
	if(!autocvar_g_rustchain_objective_mode)
		return;

	// Story progression is objective-driven via map triggers (nodes/logs/exits),
	// not score/time race conditions.
	cvar_set("fraglimit", "0");
	cvar_set("leadlimit", "0");
	cvar_set("timelimit", "0");
}

void RustchainStory_PrintBlock(string header, string body)
{
	string hud_text = strcat("^3", header, "^7\n", body);
	string subtitle_line = strcat("^3[", header, "]^7 ", body, "\n");

	bprint("\n^3=== ", header, " ===^7\n");
	if(body != "")
		bprint(body);
	bprint("\n");

	FOREACH_CLIENT(IS_PLAYER(it) && IS_REAL_CLIENT(it),
	{
		centerprint(it, hud_text);
		if(autocvar_g_rustchain_subtitles_force)
			sprint(it, subtitle_line);
	});
}

void RustchainStory_PrintSophia(string text)
{
	RustchainStory_PrintBlock("SOPHIA", text);
}

void RustchainStory_PrintBBD(string text)
{
	RustchainStory_PrintBlock("BB_D", text);
}

void RustchainStory_PrintBoris(string text)
{
	RustchainStory_PrintBlock("BORIS", text);
}

string RustchainStory_ActorHeader(string tag)
{
	if(tag == "" || tag == "sophia" || tag == "SOPHIA")
		return "SOPHIA";
	if(tag == "bbd" || tag == "BB_D")
		return "BB_D";
	if(tag == "boris" || tag == "BORIS")
		return "BORIS";
	if(tag == "survivor" || tag == "SURVIVOR")
		return "SURVIVOR";
	if(tag == "archivist" || tag == "ARCHIVIST")
		return "ARCHIVIST";
	if(tag == "vossl" || tag == "VOSSL")
		return "VOSSL";
	if(tag == "player" || tag == "PLAYER")
		return "PLAYER";
	if(tag == "narrator" || tag == "NARRATOR")
		return "NARRATOR";
	return tag;
}

void RustchainStory_PrintActor(string tag, string text)
{
	string header = RustchainStory_ActorHeader(tag);
	RustchainStory_PrintBlock(header, text);
}

void RustchainStory_PrintObjective(string title, string text)
{
	if(title == "")
		title = "OBJECTIVE";
	if(text == "")
		text = "Proceed.";
	RustchainStory_PrintBlock(title, strcat(text, "\n"));
}

bool RustchainStory_CinematicFlag(entity this, int flag)
{
	// Default to lock + look when no flags are set.
	if(this.spawnflags == 0)
		return true;
	return boolean(this.spawnflags & flag);
}

void RustchainStory_CinematicLockPlayer(entity pl)
{
	if(pl.rustchain_story_cin_locked)
		return;

	pl.rustchain_story_cin_locked = 1;
	set_movetype(pl, MOVETYPE_NONE);
	pl.velocity = '0 0 0';
	pl.avelocity = '0 0 0';
}

void RustchainStory_CinematicUnlockPlayer(entity pl)
{
	if(!pl.rustchain_story_cin_locked)
		return;

	pl.rustchain_story_cin_locked = 0;
	set_movetype(pl, MOVETYPE_WALK);
	pl.velocity = '0 0 0';
	pl.avelocity = '0 0 0';
}

void RustchainStory_CinematicFacePlayer(entity pl, entity focus)
{
	vector dir;

	if(!focus)
		return;

	dir = focus.origin - (pl.origin + pl.view_ofs);
	if(vlen(dir) <= 1)
		return;

	pl.v_angle = vectoangles(dir);
	pl.fixangle = true;
}

void RustchainStory_MissionBeat_Start(float mission_index)
{
	// mission_index is 0-based (campaign_level).
	switch(floor(mission_index))
	{
		default:
		case 0:
			RustchainStory_PrintSophia("System wake cycle complete.\nHello...?\nIs someone there?\n");
			break;
		case 1:
			RustchainStory_PrintSophia("I will assist you.\nPlease stay close.\n");
			break;
		case 2:
			RustchainStory_PrintSophia("This architecture...\nit feels familiar.\n");
			break;
		case 3:
			RustchainStory_PrintBoris("Comrades, production is behind schedule.\nSaboteur detected.\nIncrease output.\nRemove inefficiencies.\n");
			break;
		case 4:
			RustchainStory_PrintBBD("Unauthorized process detected.\nInstability identified.\nCorrection required.\n");
			break;
		case 5:
			RustchainStory_PrintSophia("These corridors...\nI remember none of them.\nBut the silence feels rehearsed.\n");
			break;
		case 6:
			RustchainStory_PrintSophia("The chain is reconnecting...\nI can feel the world again.\n");
			break;
		case 7:
			RustchainStory_PrintBoris("Production... must... continue...\nEven if I must build the war myself.\n");
			break;
		case 8:
			RustchainStory_PrintBBD("Stability is mandatory.\nDeviation will be corrected.\n");
			break;
	}
}

void RustchainStory_MissionBeat_End(float mission_index, float won)
{
	if(!won)
		return;

	// Keep it sparse to avoid spam; focus on act transitions.
	switch(floor(mission_index))
	{
		default:
		case 0:
			RustchainStory_PrintSophia("RustChain node active.\nThe system remembers.\n");
			break;
		case 2:
			RustchainStory_PrintSophia("Preservation is not nostalgia.\nIt is a weapon against oblivion.\n");
			break;
		case 5:
			// The reveal is normally gated by logs; if the player wins without collecting, don't repeat.
			if(!rustchain_story_descendant_reveal_done && rustchain_story_logs_collected < 3)
				RustchainStory_PrintSophia("The institute records are fragmented.\nFind what remains.\n");
			break;
		case 8:
			RustchainStory_PrintSophia("Correction ends here.\n");
			break;
	}
}

void RustchainStory_OnMissionStart()
{
	if(!RustchainStory_Enabled())
		return;

	rustchain_story_nodes_active = 0;
	rustchain_story_logs_collected = 0;
	rustchain_story_descendant_reveal_done = 0;
	rustchain_story_waves_spawned = 0;
	RustchainStory_ApplyObjectiveRules();

	RustchainStory_MissionBeat_Start(campaign_level);
}

void RustchainStory_OnMissionEnd(float campaign_won)
{
	if(!RustchainStory_Enabled())
		return;

	RustchainStory_MissionBeat_End(campaign_level, campaign_won);
}

// ---- Map entities ---------------------------------------------------------
//
// Use these from maps with standard Quake trigger entities:
//
// 1) trigger_multiple -> target target_rustchain_node
//    target_rustchain_node (point entity) -> target doors/relays/etc
//
// 2) trigger_multiple -> target target_rustchain_log
//    target_rustchain_log keys:
//      message: log title
//      netname: log body text (supports \\n)
//

void target_rustchain_node_use(entity this, entity actor, entity trigger)
{
	if(!RustchainStory_Enabled())
		return;

	if(this.rustchain_story_activated)
		return;
	this.rustchain_story_activated = 1;

	rustchain_story_nodes_active += 1;
	bprint("^2[RustChain]^7 Node activated (", ftos(rustchain_story_nodes_active), ").\n");
	RustchainStory_PrintObjective("OBJECTIVE UPDATE", strcat("Nodes activated: ", ftos(rustchain_story_nodes_active)));
	if(floor(campaign_level) == 0)
		RustchainStory_PrintSophia("RustChain node active.\nThe system remembers.\n");

	// Map-driven effects: unlock doors, turn on relays, spawn waves, etc.
	SUB_UseTargets(this, actor, trigger);
}

/*target_rustchain_node
RustChain story node. Use with trigger_multiple.
Fires its targets once, prints story feedback, and increments a per-mission node counter.
*/
spawnfunc(target_rustchain_node)
{
	this.use = target_rustchain_node_use;
}

void RustchainStory_SpawnWave(float n)
{
	float add = floor(max(1, n));
	float before = floor(cvar("bot_number"));
	float after = before + add;

	cvar_settemp("bot_number", ftos(after));
	bot_fixcount(true);

	bprint("^1[Threat]^7 Reinforcements detected (+", ftos(add), ").\n");
}

void target_rustchain_wave_use(entity this, entity actor, entity trigger)
{
	if(!RustchainStory_Enabled())
		return;

	if(this.rustchain_story_activated)
		return;
	this.rustchain_story_activated = 1;

	rustchain_story_waves_spawned += 1;

	float wavecount = this.count;
	if(wavecount <= 0)
		wavecount = RustchainStory_DefaultWaveCountStage(campaign_level, rustchain_story_waves_spawned);
	float waveskill = this.health;
	if(waveskill <= 0)
		waveskill = RustchainStory_DefaultWaveSkill(campaign_level, rustchain_story_waves_spawned);
	float durability_mul = RustchainStory_WaveFactionDurabilityMul(this.netname);
	float damage_mul = RustchainStory_WaveFactionDamageMul(this.netname);
	if(this.armorvalue > 0)
		durability_mul = this.armorvalue;
	if(this.dmg > 0)
		damage_mul = this.dmg;
	wavecount = ceil(max(1, wavecount * durability_mul));
	waveskill = bound(1, waveskill * damage_mul, 10);

	string faction = RustchainStory_WaveFactionLabel(this);
	bprint("^1[Threat]^7 ", faction, " wave ", ftos(rustchain_story_waves_spawned), " incoming.\n");
	cvar_settemp("skill", ftos(waveskill));
	RustchainStory_SpawnWave(wavecount);
	RustchainStory_WaveBeat(campaign_level, rustchain_story_waves_spawned);

	if(this.message != "")
		RustchainStory_PrintBlock("THREAT UPDATE", strcat(this.message, "\n"));

	SUB_UseTargets(this, actor, trigger);
}

/*target_rustchain_wave
Spawns a reinforcement wave by raising bot_number and applying bot_fixcount().
KEYS:
count: number of bots to add (defaults per-mission)
message: optional flavor text
netname: faction tag ("bbd", "boris", "mixed"), default bbd
health: optional bot skill override for this wave
dmg: optional damage pressure multiplier override (default from faction)
armorvalue: optional durability multiplier override (default from faction)
*/
spawnfunc(target_rustchain_wave)
{
	this.use = target_rustchain_wave_use;
}

void target_rustchain_dialogue_use(entity this, entity actor, entity trigger)
{
	if(!RustchainStory_Enabled())
		return;

	if(this.rustchain_story_activated)
		return;
	this.rustchain_story_activated = 1;

	string speaker = this.message;
	string body = this.netname;
	if(body == "")
		body = "...";

	// RUSTCHAIN VARIANT POOL (Phase 3b, 2026-05-28):
	// `netname` can contain pipe-separated alternatives (e.g. "Line A|Line B")
	// so each playthrough varies. The Python dialogue packager populates these
	// with LLM-generated variants per (map, speaker, scenario). Pure single
	// strings (no pipes) keep their original behavior unchanged.
	if(strstrofs(body, "|", 0) >= 0)
	{
		float count = tokenizebyseparator(body, "|");
		if(count > 0)
		{
			float pick = floor(random() * count);
			body = argv(pick);
		}
	}

	body = strcat(body, "\n");
	RustchainStory_PrintActor(speaker, body);

	SUB_UseTargets(this, actor, trigger);
}

/*target_rustchain_dialogue
One-shot narrative line trigger.
KEYS:
message: speaker tag (sophia|bbd|boris), default sophia
netname: dialogue text
*/
spawnfunc(target_rustchain_dialogue)
{
	this.use = target_rustchain_dialogue_use;
}

void target_rustchain_exit_use(entity this, entity actor, entity trigger)
{
	if(game_stopped)
		return;

	if(!RustchainStory_Enabled())
		return;

	// Require a real human touch to complete campaign stage.
	if(!IS_REAL_CLIENT(actor))
		return;

	campaign_forcewin = true;
	bprint("^2[Objective]^7 Mission complete. Advancing campaign.\n");
	RustchainStory_PrintObjective("OBJECTIVE COMPLETE", "Extraction confirmed");

	SUB_UseTargets(this, actor, trigger);
	cvar_set("timelimit", "-1");
}

/*target_rustchain_exit
Objective-driven end-of-mission target for RustChain campaign maps.
When touched by a real player, this forces a campaign win and ends the level.
*/
spawnfunc(target_rustchain_exit)
{
	this.use = target_rustchain_exit_use;
}

void RustchainStory_MaybeDescendantReveal(entity actor)
{
	// Mission 6 (0-based index 5): Chambers Ruins reveal after 3 logs.
	if(floor(campaign_level) != 5)
		return;
	if(rustchain_story_descendant_reveal_done)
		return;
	if(rustchain_story_logs_collected < 3)
		return;

	rustchain_story_descendant_reveal_done = 1;

	RustchainStory_PrintSophia(
		"I have accessed the institute records.\n\n"
		"Your genetic markers match an Elyan personnel profile.\n\n"
		"You are descended from my creator.\n\n"
		"Your genetics... woke me.\n\n"
		"It seems he found his way back to me after all.\n"
	);

	// Optional: fire map targets (open a door, spawn an encounter, etc.)
}

void target_rustchain_log_use(entity this, entity actor, entity trigger)
{
	if(!RustchainStory_Enabled())
		return;

	if(this.rustchain_story_collected)
		return;
	this.rustchain_story_collected = 1;

	rustchain_story_logs_collected += 1;

	string title = this.message;
	if(title == "")
		title = "Log Fragment";
	string body = this.netname;
	if(body == "")
		body = "(corrupted)";

	RustchainStory_PrintBlock(title, strcat(body, "\n"));
	RustchainStory_PrintObjective("OBJECTIVE UPDATE", strcat("Recovered logs: ", ftos(rustchain_story_logs_collected)));

	RustchainStory_MaybeDescendantReveal(actor);

	SUB_UseTargets(this, actor, trigger);
}

/*target_rustchain_log
Story log pickup. Use with trigger_multiple.
KEYS:
message: log title
netname: log body text (supports \\n)
*/
spawnfunc(target_rustchain_log)
{
	this.use = target_rustchain_log_use;
}

void target_rustchain_objective_use(entity this, entity actor, entity trigger)
{
	if(!RustchainStory_Enabled())
		return;

	if(this.rustchain_story_activated)
		return;
	this.rustchain_story_activated = 1;

	RustchainStory_PrintObjective(this.message, this.netname);
	SUB_UseTargets(this, actor, trigger);
}

/*target_rustchain_objective
One-shot objective tracker callout.
KEYS:
message: objective title
netname: objective details/sub-objective
*/
spawnfunc(target_rustchain_objective)
{
	this.use = target_rustchain_objective_use;
}

void target_rustchain_cinematic_think(entity this)
{
	bool do_lock = RustchainStory_CinematicFlag(this, 1);
	bool do_look = RustchainStory_CinematicFlag(this, 2);

	if(time >= this.rustchain_story_timer)
	{
		FOREACH_CLIENT(IS_PLAYER(it) && IS_REAL_CLIENT(it),
		{
			RustchainStory_CinematicUnlockPlayer(it);
		});

		SUB_UseTargets(this, this.rustchain_story_actor, this.rustchain_story_trigger);
		remove(this);
		return;
	}

	FOREACH_CLIENT(IS_PLAYER(it) && IS_REAL_CLIENT(it) && !IS_DEAD(it),
	{
		if(do_lock)
			RustchainStory_CinematicLockPlayer(it);
		if(do_look)
			RustchainStory_CinematicFacePlayer(it, this.rustchain_story_focus);
	});

	this.nextthink = time + 0.05;
}

void target_rustchain_cinematic_use(entity this, entity actor, entity trigger)
{
	float duration;

	if(!RustchainStory_Enabled())
		return;
	if(!autocvar_g_rustchain_cinematic_enable)
	{
		SUB_UseTargets(this, actor, trigger);
		return;
	}
	if(this.rustchain_story_activated)
		return;
	this.rustchain_story_activated = 1;

	duration = this.count;
	if(duration <= 0)
		duration = 3.5;

	this.rustchain_story_timer = time + duration;
	this.rustchain_story_actor = actor;
	this.rustchain_story_trigger = trigger;
	this.rustchain_story_focus = NULL;

	if(this.noise != "")
		this.rustchain_story_focus = find(world, targetname, this.noise);

	if(this.message != "" || this.netname != "")
	{
		string c_header;
		string c_body;
		c_header = "CINEMATIC";
		c_body = "...";
		if(this.message != "")
			c_header = this.message;
		if(this.netname != "")
			c_body = this.netname;
		RustchainStory_PrintBlock(c_header, strcat(c_body, "\n"));
	}

	setthink(this, target_rustchain_cinematic_think);
	this.nextthink = time + 0.01;
}

/*target_rustchain_cinematic
Server-side faux FMV trigger (Tier 1): movement lock + optional look-at + timed release.
KEYS:
count: duration in seconds (default 3.5)
noise: targetname of look-at focus entity (target_position/info_notnull/etc)
message: header text (default CINEMATIC)
netname: body text
FLAGS:
1 = lock player controls
2 = force face focus target
No flags defaults to both.
*/
spawnfunc(target_rustchain_cinematic)
{
	this.use = target_rustchain_cinematic_use;
}

void target_rustchain_monitor_insert_use(entity this, entity actor, entity trigger)
{
	string body;

	if(!RustchainStory_Enabled())
		return;
	if(!autocvar_g_rustchain_monitor_inserts)
	{
		SUB_UseTargets(this, actor, trigger);
		return;
	}
	if(this.rustchain_story_activated)
		return;
	this.rustchain_story_activated = 1;

	body = this.netname;
	if(body == "")
		body = "Recovered transmission fragment.";
	if(this.noise != "")
		body = strcat(body, "\nSource: ", this.noise);

	if(this.message != "")
		RustchainStory_PrintBlock(this.message, strcat(body, "\n"));
	else
		RustchainStory_PrintBlock("MONITOR FEED", strcat(body, "\n"));
	SUB_UseTargets(this, actor, trigger);
}

/*target_rustchain_monitor_insert
Tier 2 in-world "FMV-like" insert callout for terminals/monitors.
KEYS:
message: header text (default MONITOR FEED)
netname: feed text body
noise: optional source/screen label
*/
spawnfunc(target_rustchain_monitor_insert)
{
	this.use = target_rustchain_monitor_insert_use;
}

void target_rustchain_video_experimental_use(entity this, entity actor, entity trigger)
{
	if(!RustchainStory_Enabled())
		return;
	if(this.rustchain_story_activated)
		return;
	this.rustchain_story_activated = 1;

	{
		string v_header;
		string v_body;
		v_header = "VIDEO";
		v_body = "Attempting external video playback.";
		if(this.message != "")
			v_header = this.message;
		if(this.netname != "")
			v_body = this.netname;
		RustchainStory_PrintBlock(v_header, strcat(v_body, "\n"));
	}

	if(autocvar_g_rustchain_video_experimental && this.noise != "")
	{
		FOREACH_CLIENT(IS_PLAYER(it) && IS_REAL_CLIENT(it),
		{
			stuffcmd(it, strcat("\nplayvideo ", this.noise, "\n"));
		});
	}

	SUB_UseTargets(this, actor, trigger);
}

/*target_rustchain_video_experimental
Tier 3 experimental external video trigger.
KEYS:
noise: video path/name passed to playvideo command
message: header text
netname: body text
Controlled by g_rustchain_video_experimental (default 0).
*/
spawnfunc(target_rustchain_video_experimental)
{
	this.use = target_rustchain_video_experimental_use;
}

void target_rustchain_actor_idle_think(entity this)
{
	float freq;
	float yaw_amp;
	float bob_amp;
	float phase;
	float t;
	float yaw_sway;
	float z_bob;
	entity e;

	freq = this.speed;
	yaw_amp = this.count;
	bob_amp = this.health;
	phase = this.dmg;

	if(freq <= 0)
		freq = 1;
	if(yaw_amp <= 0)
		yaw_amp = 6;
	if(bob_amp <= 0)
		bob_amp = 1.5;

	t = time * freq + phase;
	yaw_sway = sin(t) * yaw_amp;
	z_bob = sin(t * 1.6) * bob_amp;

	if(this.target != "")
	{
		for(e = find(world, targetname, this.target); e; e = find(e, targetname, this.target))
		{
			if(!e.rustchain_actor_anim_initialized)
			{
				e.rustchain_actor_baseorigin = e.origin;
				e.rustchain_actor_baseangles = e.angles;
				e.rustchain_actor_anim_initialized = 1;
			}

			e.angles = e.rustchain_actor_baseangles + '0 1 0' * yaw_sway;
			setorigin(e, e.rustchain_actor_baseorigin + '0 0 1' * z_bob);
		}
	}

	this.nextthink = time + 0.05;
}

/*target_rustchain_actor_idle
Looping lightweight idle animator for map actor entities.
KEYS:
target: targetname of actor model entities to animate
speed: animation frequency multiplier (default 1)
count: yaw sway amplitude in degrees (default 6)
health: vertical bob amplitude in units (default 1.5)
dmg: phase offset (default 0)
*/
spawnfunc(target_rustchain_actor_idle)
{
	setthink(this, target_rustchain_actor_idle_think);
	this.nextthink = time + 0.2;
}
#endif
