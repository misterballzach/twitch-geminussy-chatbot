
interface TwitchUser {
  id: string;
  login: string;
  display_name: string;
}

export const getTwitchAuthUrl = (): string => {
  return 'https://twitchtokengenerator.com/';
};

export const fetchTwitchUser = async (token: string, clientId: string): Promise<TwitchUser | null> => {
  try {
    const response = await fetch('https://api.twitch.tv/helix/users', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Client-Id': clientId,
      },
    });

    if (!response.ok) {
      // Provide more detailed error info for debugging
      const errorText = await response.text();
      console.error(`Twitch API Error: ${response.status}`, errorText);
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
