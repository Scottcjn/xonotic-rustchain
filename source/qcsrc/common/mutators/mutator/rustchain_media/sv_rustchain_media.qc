// RustChain Media System - Server Implementation
// Video player and Sophia music for RustChain themed maps
// + RustChain blockchain announcements via Sophia voice

#include "sv_rustchain_media.qh"

#ifdef SVQC

#include <server/client.qh>

// ============================================================================
// RUSTCHAIN API CONFIGURATION
// ============================================================================

// URI ID for RustChain API callbacks (between URI_GET_TOS=34 and URI_GET_URLLIB=128)
const int URI_GET_RUSTCHAIN = 50;

// RustChain node API endpoint
string autocvar_g_rustchain_api_url = "http://50.28.86.131:8088";

// Polling interval in seconds
float autocvar_g_rustchain_poll_interval = 30;

// Enable/disable blockchain announcements
bool autocvar_g_rustchain_announcements = true;

// ============================================================================
// RUSTCHAIN STATE TRACKING
// ============================================================================

// Last known blockchain state (to detect changes)
int rustchain_last_block_height;
int rustchain_last_epoch;
int rustchain_last_miner_count;
float rustchain_last_poll_time;
bool rustchain_api_initialized;

// Announcement queue (simple FIFO)
string rustchain_announce_queue[8];
int rustchain_queue_head;
int rustchain_queue_tail;
float rustchain_last_announce_time;

// ============================================================================
// ANNOUNCEMENT SOUND MAPPINGS
// ============================================================================

// Sound files in sound/announcer/sophia/rustchain/
// These need to be generated with XTTS
void RustChain_PlayAnnouncement(string event_type)
{
	string soundfile = "";

	if (event_type == "block_mined")
		soundfile = "announcer/sophia/rustchain/block_confirmed.ogg";
	else if (event_type == "epoch_complete")
		soundfile = "announcer/sophia/rustchain/epoch_settlement.ogg";
	else if (event_type == "miner_joined")
		soundfile = "announcer/sophia/rustchain/miner_joined.ogg";
	else if (event_type == "rtc_reward")
		soundfile = "announcer/sophia/rustchain/rtc_reward.ogg";
	else if (event_type == "poa_active")
		soundfile = "announcer/sophia/rustchain/poa_active.ogg";
	else if (event_type == "g4_bonus")
		soundfile = "announcer/sophia/rustchain/g4_vintage_bonus.ogg";
	else if (event_type == "g5_bonus")
		soundfile = "announcer/sophia/rustchain/g5_hardware.ogg";
	else if (event_type == "network_healthy")
		soundfile = "announcer/sophia/rustchain/network_healthy.ogg";

	if (soundfile == "")
		return;

	// Play to all clients via stuffcmd (uses external player path we set up)
	FOREACH_CLIENT(IS_REAL_CLIENT(it), {
		stuffcmd(it, strcat("play ", soundfile, "\n"));
	});

	LOG_INFO("[RUSTCHAIN] Announcement: ", event_type);
}

// Queue an announcement (to avoid spamming)
void RustChain_QueueAnnouncement(string event_type)
{
	int next_tail = (rustchain_queue_tail + 1) % 8;
	if (next_tail == rustchain_queue_head)
	{
		// Queue full, skip
		return;
	}
	rustchain_announce_queue[rustchain_queue_tail] = strzone(event_type);
	rustchain_queue_tail = next_tail;
}

// Process announcement queue (call periodically)
void RustChain_ProcessAnnouncementQueue()
{
	// Only announce every 3 seconds to avoid spam
	if (time - rustchain_last_announce_time < 3)
		return;

	if (rustchain_queue_head == rustchain_queue_tail)
		return;  // Queue empty

	string event_type = rustchain_announce_queue[rustchain_queue_head];
	RustChain_PlayAnnouncement(event_type);
	strunzone(rustchain_announce_queue[rustchain_queue_head]);
	rustchain_announce_queue[rustchain_queue_head] = "";
	rustchain_queue_head = (rustchain_queue_head + 1) % 8;
	rustchain_last_announce_time = time;
}

// ============================================================================
// RUSTCHAIN API POLLING
// ============================================================================

// Start a poll to RustChain API
void RustChain_PollAPI()
{
	if (!autocvar_g_rustchain_announcements)
		return;

	// Use /epoch endpoint which has: epoch, slot, enrolled_miners
	string url = strcat(autocvar_g_rustchain_api_url, "/epoch");
	LOG_INFO("[RUSTCHAIN] Polling API: ", url);
	uri_get(url, URI_GET_RUSTCHAIN);
}

// Extract number after a JSON key (basic parsing since QuakeC has no JSON parser)
// Looks for "key": and extracts the number that follows
int RustChain_ExtractInt(string data, string key)
{
	string search = strcat("\"", key, "\":");
	int pos = strstrofs(data, search, 0);
	if (pos < 0)
		return -1;

	// Skip past the key and colon
	pos += strlen(search);

	// Skip whitespace
	while (pos < strlen(data) && substring(data, pos, 1) == " ")
		pos++;

	// Extract digits
	string numstr = "";
	int i;
	for (i = 0; i < 10; i++)
	{
		string ch = substring(data, pos + i, 1);
		if (ch == "" || strstrofs("0123456789", ch, 0) < 0)
			break;
		numstr = strcat(numstr, ch);
	}

	if (numstr == "")
		return -1;

	return stof(numstr);
}

// Parse RustChain /epoch response
// Format: {"blocks_per_epoch":144,"enrolled_miners":5,"epoch":7,"epoch_pot":1.5,"slot":1009}
void RustChain_ParseResponse(string data)
{
	int new_slot = RustChain_ExtractInt(data, "slot");
	int new_epoch = RustChain_ExtractInt(data, "epoch");
	int new_miners = RustChain_ExtractInt(data, "enrolled_miners");

	LOG_INFO("[RUSTCHAIN] Parsed - slot:", ftos(new_slot), " epoch:", ftos(new_epoch), " miners:", ftos(new_miners));

	// First poll - just store state, don't announce
	if (!rustchain_api_initialized)
	{
		rustchain_last_block_height = new_slot;  // slot = block height in RustChain
		rustchain_last_epoch = new_epoch;
		rustchain_last_miner_count = new_miners;
		rustchain_api_initialized = true;
		LOG_INFO("[RUSTCHAIN] API initialized - slot:", ftos(new_slot), " epoch:", ftos(new_epoch), " miners:", ftos(new_miners));
		RustChain_QueueAnnouncement("poa_active");
		return;
	}

	// Check for changes and queue announcements
	// New slot = new block confirmed
	if (new_slot > rustchain_last_block_height)
	{
		// Only announce if multiple slots passed (avoid spam on fast blocks)
		if (new_slot > rustchain_last_block_height + 5)
		{
			LOG_INFO("[RUSTCHAIN] New blocks confirmed! ", ftos(rustchain_last_block_height), " -> ", ftos(new_slot));
			RustChain_QueueAnnouncement("block_mined");
		}
		rustchain_last_block_height = new_slot;
	}

	// New epoch = settlement occurred
	if (new_epoch > rustchain_last_epoch)
	{
		LOG_INFO("[RUSTCHAIN] Epoch complete! ", ftos(rustchain_last_epoch), " -> ", ftos(new_epoch));
		RustChain_QueueAnnouncement("epoch_complete");
		RustChain_QueueAnnouncement("rtc_reward");
		rustchain_last_epoch = new_epoch;
	}

	// Miner count changes
	if (new_miners > rustchain_last_miner_count)
	{
		LOG_INFO("[RUSTCHAIN] New miner joined! ", ftos(rustchain_last_miner_count), " -> ", ftos(new_miners));
		RustChain_QueueAnnouncement("miner_joined");
		rustchain_last_miner_count = new_miners;
	}
	else if (new_miners < rustchain_last_miner_count)
	{
		rustchain_last_miner_count = new_miners;
	}
}

// ============================================================================
// SOPHIA MUSIC SYSTEM (existing)
// ============================================================================

// Sophia music tracks - just the filename, music command handles the path
string SOPHIA_TRACKS[] = {
	"fragqueen",
	"rustchainrevolution",
	"firstworldaiproblems",
	"swampgirl"
};
int SOPHIA_TRACK_COUNT = 4;

// Track durations in seconds (approximate)
float SOPHIA_TRACK_DURATIONS[] = {
	180,  // fragqueen ~3 min
	210,  // rustchainrevolution ~3.5 min
	195,  // firstworldaiproblems ~3.25 min
	240   // swampgirl ~4 min
};

// Track if music has been started this match
bool rustchain_music_started;
float rustchain_music_start_time;
int rustchain_current_track;
float rustchain_track_end_time;

// Register the mutator
REGISTER_MUTATOR(rustchain_media, cvar("g_rustchain_media"))
{
	MUTATOR_ONADD
	{
		LOG_INFO("[RUSTCHAIN] RustChain Media System Activated!");
		LOG_INFO("[RUSTCHAIN] - Sophia music will auto-play on match start");
		rustchain_music_started = false;
	}
	MUTATOR_ONREMOVE
	{
		LOG_INFO("[RUSTCHAIN] RustChain Media System Deactivated");
	}
}

// Play a video to all clients
void RustchainMedia_PlayVideo(string videoname)
{
	// Send playvideo command to all clients
	FOREACH_CLIENT(IS_REAL_CLIENT(it), {
		stuffcmd(it, strcat("playvideo ", videoname, "\n"));
	});
	LOG_INFO("[RUSTCHAIN] Playing video: ", videoname);
}

// Stop video playback
void RustchainMedia_StopVideo()
{
	FOREACH_CLIENT(IS_REAL_CLIENT(it), {
		stuffcmd(it, "stopvideo\n");
	});
	LOG_INFO("[RUSTCHAIN] Video stopped");
}

// Stop any currently playing music (including default Xonotic map music)
void RustchainMedia_StopDefaultMusic()
{
	FOREACH_CLIENT(IS_REAL_CLIENT(it), {
		// Stop CD music (map cdtrack)
		stuffcmd(it, "cd stop\n");
		// Also stop any bgmvolume to be sure
		stuffcmd(it, "stopsound\n");
	});
	LOG_INFO("[RUSTCHAIN] Stopped default music");
}

// Play background music to all clients
// DarkPlaces uses "cd play" command for music files in the music/ folder
void RustchainMedia_PlayMusic(string trackname)
{
	// First stop any default map music
	RustchainMedia_StopDefaultMusic();

	// Small delay then play our track
	// Use "cd play" command - plays files from music/ folder
	// Format: cd play trackname (without extension, it will find .ogg/.wav)
	FOREACH_CLIENT(IS_REAL_CLIENT(it), {
		stuffcmd(it, strcat("cd play ", trackname, "\n"));
	});
	LOG_INFO("[RUSTCHAIN] Playing music: ", trackname);
}

// Play a specific Sophia track by index
void RustchainMedia_PlayTrack(int track_index)
{
	if (track_index < 0 || track_index >= SOPHIA_TRACK_COUNT)
		track_index = 0;

	string track = SOPHIA_TRACKS[track_index];
	RustchainMedia_PlayMusic(track);

	// Set the end time for this track
	rustchain_current_track = track_index;
	rustchain_track_end_time = time + SOPHIA_TRACK_DURATIONS[track_index];

	LOG_INFO("[RUSTCHAIN] Playing Sophia track ", ftos(track_index + 1), "/", ftos(SOPHIA_TRACK_COUNT), ": ", track);
}

// Play a random Sophia track
void RustchainMedia_PlayRandomSophia()
{
	int track_index = floor(random() * SOPHIA_TRACK_COUNT);
	RustchainMedia_PlayTrack(track_index);
}

// Play the next track in sequence
void RustchainMedia_PlayNextTrack()
{
	int next_track = (rustchain_current_track + 1) % SOPHIA_TRACK_COUNT;
	RustchainMedia_PlayTrack(next_track);
}

// Stop music playback
void RustchainMedia_StopMusic()
{
	FOREACH_CLIENT(IS_REAL_CLIENT(it), {
		stuffcmd(it, "cd stop\n");
	});
	LOG_INFO("[RUSTCHAIN] Music stopped");
}

// Play a sound to all clients (for ambient effects)
void RustchainMedia_PlayAmbient(string soundpath)
{
	FOREACH_CLIENT(IS_REAL_CLIENT(it), {
		stuffcmd(it, strcat("play ", soundpath, "\n"));
	});
	LOG_INFO("[RUSTCHAIN] Playing ambient: ", soundpath);
}

// Hook: When a client connects, start music if not already playing
MUTATOR_HOOKFUNCTION(rustchain_media, ClientConnect)
{
	entity player = M_ARGV(0, entity);

	LOG_INFO("[RUSTCHAIN] ClientConnect hook fired for: ", player.netname);

	// Start music on first real client connect if not already started
	if (!rustchain_music_started && IS_REAL_CLIENT(player))
	{
		rustchain_music_started = true;
		rustchain_music_start_time = time;
		LOG_INFO("[RUSTCHAIN] Starting music for first client...");
		RustchainMedia_PlayRandomSophia();
	}

	// Initialize RustChain API polling on first client connect
	if (!rustchain_api_initialized && autocvar_g_rustchain_announcements && IS_REAL_CLIENT(player))
	{
		LOG_INFO("[RUSTCHAIN] First client connected, starting API polling...");
		rustchain_last_poll_time = time - autocvar_g_rustchain_poll_interval + 5;  // Poll in 5 seconds
	}

	return false;
}

// Also try PlayerSpawn as backup
MUTATOR_HOOKFUNCTION(rustchain_media, PlayerSpawn)
{
	entity player = M_ARGV(0, entity);

	LOG_INFO("[RUSTCHAIN] PlayerSpawn hook fired for: ", player.netname);

	// Start music on first player spawn if not already started
	if (!rustchain_music_started && IS_REAL_CLIENT(player))
	{
		rustchain_music_started = true;
		rustchain_music_start_time = time;
		LOG_INFO("[RUSTCHAIN] Starting music from PlayerSpawn...");
		RustchainMedia_PlayRandomSophia();
	}
}

// Hook: Check if track ended and play next one
MUTATOR_HOOKFUNCTION(rustchain_media, PlayerRegen)
{
	// Only check once per second to avoid spam
	static float last_check_time;
	if (time - last_check_time < 1)
		return false;
	last_check_time = time;

	// Check if music is playing and track has ended
	if (rustchain_music_started && rustchain_track_end_time > 0 && time >= rustchain_track_end_time)
	{
		LOG_INFO("[RUSTCHAIN] Track ended, cycling to next...");
		RustchainMedia_PlayNextTrack();
	}

	return false;
}

// Hook: Reset music state on match restart
MUTATOR_HOOKFUNCTION(rustchain_media, reset_map_global)
{
	// Reset music for new round - will play again on first spawn
	rustchain_music_started = false;
}

// ============================================================================
// RUSTCHAIN API CALLBACK AND POLLING HOOKS
// ============================================================================

// Hook: Handle URI callback from RustChain API
MUTATOR_HOOKFUNCTION(rustchain_media, URI_GetCallback)
{
	int id = M_ARGV(0, float);
	float status = M_ARGV(1, float);
	string data = M_ARGV(2, string);

	if (id != URI_GET_RUSTCHAIN)
		return false;  // Not our callback

	if (status != 0)
	{
		LOG_INFO("[RUSTCHAIN] API error, status: ", ftos(status));
		return true;  // Handled (even if error)
	}

	LOG_INFO("[RUSTCHAIN] API response received");
	RustChain_ParseResponse(data);
	return true;  // Handled
}

// Hook: Periodic polling using PlayerRegen (runs frequently on active server)
MUTATOR_HOOKFUNCTION(rustchain_media, PlayerPreThink)
{
	// Only run checks once per frame, not per player
	static float last_frame_time;
	if (time == last_frame_time)
		return false;
	last_frame_time = time;

	// Process announcement queue
	RustChain_ProcessAnnouncementQueue();

	// Poll RustChain API periodically
	if (autocvar_g_rustchain_announcements)
	{
		if (time - rustchain_last_poll_time >= autocvar_g_rustchain_poll_interval)
		{
			rustchain_last_poll_time = time;
			RustChain_PollAPI();
		}
	}

	return false;
}

#endif
