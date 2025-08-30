// IMPORTANT: This public Client ID is intended for development and demonstration purposes.
const TWITCH_CLIENT_ID = 'kimne78kx3ncx6brgo4mv6wki5h1ko';
// This is a known, whitelisted redirect URI for the public client ID above.
// Even though the page itself is discontinued, the redirect is still valid for the OAuth flow,
// which is crucial for getting a token that works with the client ID.
const REDIRECT_URI = 'https://twitchapps.com/tmi/';


interface TwitchUser {
  id: string;
  login: string;
  display_name: string;
}

export const getTwitchAuthUrl = (): string => {
  const params = new URLSearchParams({
    client_id: TWITCH_CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    response_type: 'token',
    scope: 'chat:read chat:edit',
  });
  return `https://id.twitch.tv/oauth2/authorize?${params.toString()}`;
};

export const fetchTwitchUser = async (token: string): Promise<TwitchUser | null> => {
  try {
    const response = await fetch('https://api.twitch.tv/helix/users', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Client-Id': TWITCH_CLIENT_ID,
      },
    });

    if (!response.ok) {
      throw new Error(`Twitch API responded with ${response.status}`);
    }

    const data = await response.json();
    if (data.data && data.data.length > 0) {
      return data.data[0];
    }
    return null;
  } catch (error) {
    console.error("Failed to fetch Twitch user:", error);
    return null;
  }
};