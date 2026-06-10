// RustChain Media System - Client Implementation
// HUD overlay for RustChain PoA integration
// Features: Boot logo, RTC balance, network stats, kill rewards, vintage badge

#include "cl_rustchain_media.qh"

#ifdef CSQC

#include <client/draw.qh>
#include <common/stats.qh>

// Register client-side mutator
REGISTER_MUTATOR(rustchain_media, true);

// ============================================================================
// CVARS
// ============================================================================
float autocvar_cl_rustchain_hud = 1;           // Enable RustChain HUD elements
float autocvar_cl_rustchain_boot_logo = 1;     // Show boot logo on connect
float autocvar_cl_rustchain_boot_duration = 3; // Boot logo display time

// ============================================================================
// STATE VARIABLES
// ============================================================================

// Boot/startup logo
float rustchain_boot_start_time;
float rustchain_boot_shown;

// RustChain branding display
float rustchain_logo_alpha;
float rustchain_logo_time;

// RTC Balance (received from server or local tracking)
float rustchain_rtc_balance;
float rustchain_rtc_balance_display;  // Smoothly animated display value

// Network stats (polled from server announcements)
int rustchain_network_epoch;
int rustchain_network_slot;
int rustchain_network_miners;

// Kill reward popup system
string rustchain_reward_text;
float rustchain_reward_time;
float rustchain_reward_amount;

// Vintage hardware badge
string rustchain_hw_badge;
float rustchain_hw_multiplier;

// ============================================================================
// INITIALIZATION
// ============================================================================

void RustchainMedia_Init()
{
	rustchain_video_playing = false;
	rustchain_logo_alpha = 1.0;
	rustchain_logo_time = time;
	rustchain_boot_start_time = time;
	rustchain_boot_shown = false;
	rustchain_rtc_balance = 0;
	rustchain_rtc_balance_display = 0;
	rustchain_hw_badge = "";
	rustchain_hw_multiplier = 1.0;
}

// ============================================================================
// BOOT LOGO - Shows on game start/connect
// ============================================================================

void RustchainMedia_DrawBootLogo()
{
	if (!autocvar_cl_rustchain_boot_logo)
		return;

	float elapsed = time - rustchain_boot_start_time;
	if (elapsed > autocvar_cl_rustchain_boot_duration)
		return;

	// Calculate fade: fade in for 0.5s, hold, fade out for 0.5s
	float alpha = 1.0;
	if (elapsed < 0.5)
		alpha = elapsed / 0.5;
	else if (elapsed > autocvar_cl_rustchain_boot_duration - 0.5)
		alpha = (autocvar_cl_rustchain_boot_duration - elapsed) / 0.5;

	vector screen_size = vec2(vid_conwidth, vid_conheight);

	// Draw dark overlay
	drawfill('0 0 0', screen_size, '0 0 0', alpha * 0.85, DRAWFLAG_NORMAL);

	// Draw centered boot logo (512x512 scaled to fit)
	vector logo_size = '256 256 0';
	vector logo_pos;
	logo_pos.x = (screen_size.x - logo_size.x) / 2;
	logo_pos.y = (screen_size.y - logo_size.y) / 2 - 40;
	logo_pos.z = 0;

	drawpic(logo_pos, "gfx/rustchain/logo_boot", logo_size, '1 1 1', alpha, DRAWFLAG_NORMAL);

	// Draw "Connecting to RustChain Network..." text
	string text = "Connecting to RustChain Network...";
	vector text_size = '10 10 0';
	vector text_pos;
	text_pos.x = (screen_size.x - stringwidth(text, false, text_size)) / 2;
	text_pos.y = logo_pos.y + logo_size.y + 20;
	text_pos.z = 0;

	// Pulsing amber color
	float pulse = 0.7 + 0.3 * sin(time * 3);
	drawstring(text_pos, text, text_size, '0.9 0.65 0.2' * pulse, alpha, DRAWFLAG_NORMAL);
}

// ============================================================================
// RTC BALANCE DISPLAY - Top right corner
// ============================================================================

void RustchainMedia_DrawRTCBalance()
{
	if (!autocvar_cl_rustchain_hud)
		return;

	// Smooth animation towards actual balance
	rustchain_rtc_balance_display += (rustchain_rtc_balance - rustchain_rtc_balance_display) * frametime * 5;

	vector screen_size = vec2(vid_conwidth, vid_conheight);

	// Position: top right
	vector pos;
	pos.x = screen_size.x - 140;
	pos.y = 60;
	pos.z = 0;

	// Draw small logo icon
	drawpic(pos, "gfx/rustchain/logo_small", '24 24 0', '1 1 1', 0.9, DRAWFLAG_NORMAL);

	// Draw RTC amount
	string balance_str = sprintf("%.4f RTC", rustchain_rtc_balance_display);
	vector text_pos = pos;
	text_pos.x += 28;
	text_pos.y += 5;
	drawstring(text_pos, balance_str, '12 12 0', '0.9 0.7 0.2', 0.9, DRAWFLAG_NORMAL);
}

// ============================================================================
// NETWORK STATS PANEL - Below RTC balance
// ============================================================================

void RustchainMedia_DrawNetworkStats()
{
	if (!autocvar_cl_rustchain_hud)
		return;

	vector screen_size = vec2(vid_conwidth, vid_conheight);

	// Position: below RTC balance
	vector pos;
	pos.x = screen_size.x - 140;
	pos.y = 90;
	pos.z = 0;

	// Semi-transparent background
	drawfill(pos - '4 2 0', '130 52 0', '0.1 0.05 0', 0.5, DRAWFLAG_NORMAL);

	// Network stats text
	vector text_size = '8 8 0';
	vector color = '0.7 0.5 0.15';

	string line1 = sprintf("Epoch: %d", rustchain_network_epoch);
	string line2 = sprintf("Slot: %d", rustchain_network_slot);
	string line3 = sprintf("Miners: %d", rustchain_network_miners);
	string line4 = "PoA Active";

	drawstring(pos, line1, text_size, color, 0.8, DRAWFLAG_NORMAL);
	pos.y += 10;
	drawstring(pos, line2, text_size, color, 0.8, DRAWFLAG_NORMAL);
	pos.y += 10;
	drawstring(pos, line3, text_size, color, 0.8, DRAWFLAG_NORMAL);
	pos.y += 10;

	// Pulsing "PoA Active" indicator
	float pulse = 0.6 + 0.4 * sin(time * 2);
	drawstring(pos, line4, text_size, '0.2 0.9 0.3' * pulse, 0.9, DRAWFLAG_NORMAL);
}

// ============================================================================
// KILL REWARD POPUP - Center screen when you get a kill
// ============================================================================

void RustchainMedia_TriggerReward(float amount, string reason)
{
	rustchain_reward_amount = amount;
	rustchain_reward_text = reason;
	rustchain_reward_time = time;
	rustchain_rtc_balance += amount;  // Add to local balance
}

void RustchainMedia_DrawKillReward()
{
	if (!autocvar_cl_rustchain_hud)
		return;

	float elapsed = time - rustchain_reward_time;
	if (elapsed > 2.0)
		return;

	// Animate: rise up and fade out
	float alpha = 1.0 - (elapsed / 2.0);
	float rise = elapsed * 30;

	vector screen_size = vec2(vid_conwidth, vid_conheight);

	// Center position, rising up
	vector pos;
	pos.x = screen_size.x / 2;
	pos.y = screen_size.y / 2 - 50 - rise;
	pos.z = 0;

	// Format: "+0.0100 RTC"
	string reward_str = sprintf("+%.4f RTC", rustchain_reward_amount);
	vector text_size = '16 16 0';
	pos.x -= stringwidth(reward_str, false, text_size) / 2;

	// Gold/amber color, glowing
	vector color = '1 0.8 0.2';
	drawstring(pos, reward_str, text_size, color, alpha, DRAWFLAG_NORMAL);

	// Reason text below (smaller)
	if (rustchain_reward_text != "")
	{
		vector reason_pos = pos;
		reason_pos.y += 20;
		reason_pos.x = screen_size.x / 2 - stringwidth(rustchain_reward_text, false, '10 10 0') / 2;
		drawstring(reason_pos, rustchain_reward_text, '10 10 0', '0.8 0.6 0.2', alpha * 0.8, DRAWFLAG_NORMAL);
	}
}

// ============================================================================
// VINTAGE HARDWARE BADGE - Shows multiplier for retro hardware
// ============================================================================

void RustchainMedia_SetHardwareBadge(string badge, float multiplier)
{
	rustchain_hw_badge = badge;
	rustchain_hw_multiplier = multiplier;
}

void RustchainMedia_DrawVintageBadge()
{
	if (!autocvar_cl_rustchain_hud)
		return;

	if (rustchain_hw_badge == "" || rustchain_hw_multiplier <= 1.0)
		return;

	// Position: top left, below other HUD elements
	vector pos;
	pos.x = 10;
	pos.y = 100;
	pos.z = 0;

	// Badge background
	drawfill(pos - '2 2 0', '100 24 0', '0.15 0.08 0', 0.6, DRAWFLAG_NORMAL);

	// Badge icon/text
	string badge_str = sprintf("%s %.1fx", rustchain_hw_badge, rustchain_hw_multiplier);

	// Color based on multiplier (higher = more golden)
	vector color;
	if (rustchain_hw_multiplier >= 2.5)
		color = '1 0.85 0.3';  // G4 gold
	else if (rustchain_hw_multiplier >= 2.0)
		color = '0.9 0.7 0.25';  // G5 amber
	else
		color = '0.8 0.6 0.2';  // Other vintage

	drawstring(pos, badge_str, '10 10 0', color, 0.9, DRAWFLAG_NORMAL);
}

// ============================================================================
// INTERMISSION BRANDING - Shows during end-of-match
// ============================================================================

void RustchainMedia_DrawBranding()
{
	if (intermission)
	{
		vector screen_size = vec2(vid_conwidth, vid_conheight);
		vector logo_pos;
		logo_pos.x = screen_size.x - 150;
		logo_pos.y = 20;
		logo_pos.z = 0;

		// Draw logo
		drawpic(logo_pos, "gfx/rustchain/logo", '128 128 0', '1 1 1', 0.85, DRAWFLAG_NORMAL);

		// Draw "Powered by RustChain" text
		string text = "Powered by RustChain";
		vector text_pos = logo_pos;
		text_pos.y += 135;
		text_pos.x = screen_size.x - stringwidth(text, false, '8 8 0') - 20;
		drawstring(text_pos, text, '8 8 0', '0.9 0.65 0.2', 0.8, DRAWFLAG_NORMAL);

		// Draw network status
		string status = "Proof-of-Antiquity Active";
		vector status_pos = text_pos;
		status_pos.y += 12;
		status_pos.x = screen_size.x - stringwidth(status, false, '6 6 0') - 20;
		drawstring(status_pos, status, '6 6 0', '0.8 0.5 0.1', 0.6, DRAWFLAG_NORMAL);
	}
}

// ============================================================================
// MAIN DRAW FUNCTION
// ============================================================================

void RustchainMedia_Draw()
{
	// Boot logo (covers screen initially)
	RustchainMedia_DrawBootLogo();

	// Skip other HUD during boot
	float elapsed = time - rustchain_boot_start_time;
	if (elapsed < autocvar_cl_rustchain_boot_duration)
		return;

	// HUD elements during gameplay
	if (!intermission)
	{
		RustchainMedia_DrawRTCBalance();
		RustchainMedia_DrawNetworkStats();
		RustchainMedia_DrawKillReward();
		RustchainMedia_DrawVintageBadge();
	}

	// Intermission branding
	RustchainMedia_DrawBranding();
}

// ============================================================================
// HOOKS
// ============================================================================

// Hook into HUD drawing
MUTATOR_HOOKFUNCTION(rustchain_media, HUD_Draw_overlay)
{
	// Initialize boot logo on first draw
	if (!rustchain_boot_shown)
	{
		rustchain_boot_start_time = time;
		rustchain_boot_shown = true;
	}

	RustchainMedia_Draw();
	return false;
}

#endif
