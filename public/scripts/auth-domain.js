// Pure account and professional-profile response contracts.
export function isTokenResponse(value) {
  return value !== null && typeof value === "object"
    && typeof value.access_token === "string" && value.access_token.trim().length > 0
    && value.token_type === "bearer" && typeof value.expires_in === "number"
    && Number.isFinite(value.expires_in) && value.expires_in > 0
    && value.expires_in <= Number.MAX_SAFE_INTEGER / 1000;
}

export const isMfaChallenge = value => value !== null && typeof value === "object"
  && value.mfa_required === true && typeof value.challenge_token === "string" && value.challenge_token.trim().length > 0
  && Number.isSafeInteger(value.expires_in) && value.expires_in > 0 && value.expires_in <= 300
  && value.access_token === undefined && value.refresh_token === undefined;
export const isLoginResponse = value => value?.mfa_required === true ? isMfaChallenge(value) : isTokenResponse(value);

export function isIdentity(value) {
  const uuid = /^[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}$/i;
  return value !== null && typeof value === "object"
    && typeof value.id === "string" && uuid.test(value.id)
    && typeof value.email === "string" && value.email.trim().length > 0
    && typeof value.display_name === "string" && value.display_name.trim().length > 0
    && value.is_active === true && typeof value.created_at === "string"
    && Number.isFinite(Date.parse(value.created_at));
}

export function isProfile(value, userId) {
  if (!value || typeof value !== "object" || value.user_id !== userId
      || typeof value.summary !== "string" || Array.from(value.summary).length > 2000
      || !["not_informed", "junior", "mid", "senior", "lead"].includes(value.seniority)
      || !Number.isInteger(value.weekly_availability_hours) || value.weekly_availability_hours < 0
      || value.weekly_availability_hours > 168 || !Array.isArray(value.skills) || value.skills.length > 30) return false;
  const names = new Set();
  return value.skills.every(skill => {
    if (!skill || typeof skill.name !== "string" || !skill.name.trim() || Array.from(skill.name).length > 80
        || !Number.isInteger(skill.level) || skill.level < 1 || skill.level > 5) return false;
    const name = skill.name.normalize("NFC").trim().toLowerCase();
    if (names.has(name)) return false;
    names.add(name); return true;
  });
}

export function buildProfileDraft({ summary, seniority, hours, skills }) {
  const availability = Number(hours);
  if (Array.from(summary).length > 2000 || !["not_informed", "junior", "mid", "senior", "lead"].includes(seniority)
      || hours === "" || !Number.isInteger(availability) || availability < 0 || availability > 168) {
    return { error: "fields" };
  }
  if (skills.length > 30) return { error: "skills", skillIndex: 30 };
  const normalizedSkills = [], names = new Set();
  for (const [index, skill] of skills.entries()) {
    const name = skill.name.normalize("NFC").trim(), level = Number(skill.level);
    const normalized = name.toLowerCase();
    if (!name || Array.from(name).length > 80 || names.has(normalized) || !Number.isInteger(level) || level < 1 || level > 5) {
      return { error: "skills", skillIndex: index };
    }
    names.add(normalized); normalizedSkills.push({ name, level });
  }
  return { value: { summary, seniority, weekly_availability_hours: availability, skills: normalizedSkills } };
}

export const isPasswordPolicy = value => value !== null && typeof value === "object"
  && Number.isInteger(value.min_length) && value.min_length >= 12 && value.min_length <= 128 && value.max_length === 128;
export const isRegistrationResponse = value => value !== null && typeof value === "object"
  && typeof value.message === "string" && value.message.length > 0;
