import os
import time
import streamlit as st
import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from collections import OrderedDict

st.set_page_config(page_title="Detailed Discover", page_icon='📻')
#u+1F4FB

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SECRET = os.environ.get("SPOTIFY_SECRET")

client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

username = ""
scope = 'playlist-modify-public'

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,client_secret=SECRET,redirect_uri='http://192.168.1.248:8502',scope=scope))


#
# token = util.prompt_for_user_token(username, scope, redirect_uri="")
# if token:
#     sp = spotipy.Spotify(auth=token)
# else:
#     print("Can't get token for", username)






#Create application from spotify developers site and retrieve Client ID and Secret.
#Set up Spotify Client Credentials and spotipy object.
# client_credentials_manager = SpotifyClientCredentials(client_id = CLIENT_ID,
#     client_secret = SECRET)
# sp = spotipy.Spotify(client_credentials_manager = client_credentials_manager)

#List of genres accepted by recommendation endpoint
FULL_GENRE_SEED_LST = sp.recommendation_genre_seeds()['genres']

fl = '♭' #flat symbol
sh = '♯' #sharp symbol

#Mapping For Tonics
tonics = {
    -1: "No key detected ☹",
    0: "C",
    1: "C{}/D{}".format(sh,fl),
    2: "D",
    3: "D{}/E{}".format(sh,fl),
    4: "E",
    5: "F",
    6: "F{}/G{}".format(sh,fl),
    7: "G",
    8: "G/A".format(sh,fl),
    9: "A",
    10: "A{}/B{}".format(sh,fl),
    11: "B"
}

#Mapping For Modes
mode = {0: 'Min', 1: "Maj", 2: "Both"}

#SET VARIABLES FROM INITIAL SEARCH, PASSING IN CLEANED TRACK AND ARTIST
@st.cache(persist=True, allow_output_mutation=True, show_spinner=False)
def set_search_track_values(res):
    search_d = {}
    search_d['track_name'] = res['tracks']['items'][0]['name']
    search_d['track_uri'] = res['tracks']['items'][0]['uri'] #.split(":")[-1]
    search_d['arts_uri'] = [x['uri'] for x in res['tracks']['items'][0]['artists']]
    if len(res['tracks']['items'][0]['artists']) > 1:
        search_d['arts_name'] = (", ").join([x['name'] for x in res['tracks']['items'][0]['artists']])
    else:
        search_d['arts_name'] = res['tracks']['items'][0]['artists'][0]['name']
    search_d['album_uri'] = res['tracks']['items'][0]['album']['uri']
    search_d['alb_type'] = res['tracks']['items'][0]['album']['album_type']
    search_d['alb_cov'] = res['tracks']['items'][0]['album']['images'][0]['url']
    search_d['popularity'] = res['tracks']['items'][0]['popularity']
    search_d['prev_url'] = res['tracks']['items'][0]['preview_url']
    return search_d

#API CALL FOR AUDIO FEATURES FROM SEARCH TRACK
@st.cache(show_spinner=False)
def get_search_aud_feats(uri):
    search_aud_feats = sp.audio_features(uri)
    return search_aud_feats[0]


def display_track(general_d, audio_feat_d):
    col1, col2 = st.beta_columns(2)
    search_track_key = tonics[audio_feat_d['key']] + " " + mode[audio_feat_d['mode']]
    search_tempo = round(audio_feat_d['tempo'])
    #col1.markdown("![Alt Text]({})".format(general_d['alb_cov']))
    #^if this doesn't work try
    col1.image(general_d['alb_cov'], use_column_width = True)
    col2.markdown("<p style='text-align: center; font-style: italic'>{}</p>".format(general_d['track_name']), unsafe_allow_html=True)
    col2.markdown("<p style='text-align: center; font-weight: bold'>{}</p>".format(general_d['arts_name']), unsafe_allow_html=True)
    col2.markdown("<p style='text-align: center; font-weight:bold'>Tempo: <span style='font-weight: lighter'>{} BPM</span></p>".format(search_tempo),unsafe_allow_html=True)
    col2.markdown("<p style='text-align: center; font-weight:bold'>Key: <span style='font-weight: lighter'>{}</span></p>".format(search_track_key),unsafe_allow_html=True)
    col2.markdown("<p style='text-align: center; font-weight:bold'>Danceability: <span style='font-weight: lighter'>{}</span></p>".format(audio_feat_d['danceability']),unsafe_allow_html=True)
    col2.markdown("<p style='text-align: center; font-weight:bold'>Energy: <span style='font-weight: lighter'>{}</span></p>".format(audio_feat_d['energy']),unsafe_allow_html=True)
    col2.markdown("<p style='text-align: center; font-weight:bold'>Instrumentalness: <span style='font-weight: lighter'>{}</span></p>".format(audio_feat_d['instrumentalness']),unsafe_allow_html=True)
    col2.markdown("<p style='text-align: center; font-weight:bold'>Valence: <span style='font-weight: lighter'>{}</span></p>".format(audio_feat_d['valence']),unsafe_allow_html=True)
    if general_d['prev_url'] != None:
        st.audio(general_d['prev_url'], format="audio/mp3")
    else:
        st.write("Preview Unavailable ☹")
    return



#GRAB GENRES FROM THE ORIGINAL SEARCH ARTISTS CALL TO ATTEMPT TO USE
#AS SEEDS FOR RECOMMENDATION
# def get_genres(d):
#     genre_lst = sp.artists(d['arts_uri'])['artists'][0]['genres']
#     genre_seeds = [x for x in genre_lst if x in FULL_GENRE_SEED_LST]
#     return genre_seeds if len(genre_seeds) >= 1 else None

#GET TOP TRACKS FROM PRIMARY SONG'S ARTIST(S) TO USE AS SEEDS FOR RECOMMENDATION
@st.cache(show_spinner=False)
def get_tracks(d):
    top_track_uris = [d['track_uri']]
    #Retrieves top tracks for either the only artist listed on song or first two artists listed on song
    if len(d['arts_uri']) > 1:
        first_art_tracks = sp.artist_top_tracks(d['arts_uri'][0])
        first_art_tracks_uris = [x['uri'] for x in first_art_tracks['tracks'][:2]]
        sec_art_tracks = sp.artist_top_tracks(d['arts_uri'][0])
        sec_art_tracks_uris = [x['uri'] for x in sec_art_tracks['tracks'][:2]]
        first_sec = first_art_tracks_uris + sec_art_tracks_uris

        #Append artists' top two tracks and searched song into single list for seed parameter use.
        top_track_uris += first_sec
        return top_track_uris
    else:
        art_tracks = sp.artist_top_tracks(d['arts_uri'][0])
        for x in art_tracks['tracks'][:4]:
            top_track_uris.append(x['uri'])
        st.write(top_track_uris)
        return top_track_uris

#CALL FOR RELATED ARTISTS TO USE AS SEEDS FOR API'S RECOMMENDATION ENDPOINT
@st.cache(show_spinner=False)
def get_rel_arts(d):
    if len(d['arts_uri']) > 4:
        return d['arts_uri']
    else:
        rel_art_call = sp.artist_related_artists(d['arts_uri'][0])
        for x in rel_art_call['artists']:
            if len(d['arts_uri']) < 5:
                d['arts_uri'].append(x['uri'])
            else:
                break
    return d['arts_uri']

def get_filters(filt_list, audio_feat_d):

    #uses global variable to get beginning key position for filter,
    #can find a better way to do this.
    search_track_key = tonics[audio_feat_d['key']]

    #Sorting musical keys for display and selection
    sorted_song_keys = [x[1] for x in sorted(tonics.items(), key=lambda z: z[0])[1:]]

    #Creating a tuple that will hold variable keyword positional arguments
    #to later be cast to an OrderedDict and passed to recommendation endpoint
    filt_rec_params = []

    #If no filters selected, set default based on search track.
    default_filters = ['danceability','energy', 'valence']
    if not filt_list:
        for x in default_filters:
            filt_rec_params.append(('target_{}'.format(x), audio_feat_d[x]))

    #Traversing through selected filters, setting them, eventually appending to
    #the above tuple.
    else:
        for x in filt_list:
            if x == "Key":
                st.sidebar.markdown('''
                Spotify allows for Key filtering beginning at C and extending to B. This is ordinally restricted, so selections must be a single key or in an ascending range.
                ''')
                #select_slider return type is that of value parameter. A list here
                #with lower and upper bounds rendered
                key_range = st.sidebar.select_slider('Select a range for the Key(s) of Recommended Songs.', options=sorted_song_keys, value=('C',search_track_key))
                song_attr_val = list(st.sidebar.radio("Select Mode(s). 0 for Minor, 1 for Major, 2 to include both modes (only Major and Minor modes supported by Spotify API.).".format(x),['0', '1', '2']))
                song_attr_val.append(key_range)
            elif x == 'Tempo':
                tempo_range = st.sidebar.slider("Select a Tempo Range For Recommended Songs",
                round(audio_feat_d['tempo']) - 30, round(audio_feat_d['tempo']) + 30,
                (round(audio_feat_d['tempo']) - 15, round(audio_feat_d['tempo']) + 15))
                song_attr_val = tempo_range

            #Filter on any attribute that is not key or tempo
            else:
                label = "Select a Target {} For Recommended Songs. Tracks with attribute values nearest to the target will be preferred".format(x)
                song_attr_val = st.sidebar.slider(label, 0.01, 1.0, .01)

            if type(song_attr_val) == list: #will be musical key
                if song_attr_val[0] != '2':
                    filt_rec_params.extend((('min_mode',int(song_attr_val[0])), ('max_mode', int(song_attr_val[0]))))

                #Separates the dictionary's values in a list, find position of
                #the value(s) you have, and gets the key at that position
                filt_rec_params.extend((('min_key',list(tonics.keys())[list(tonics.values()).index(song_attr_val[1][0])]),
                ('max_key',list(tonics.keys())[list(tonics.values()).index(song_attr_val[1][1])])))


            elif type(song_attr_val) == tuple: #will be tempo
                filt_rec_params.extend((('min_tempo', song_attr_val[0]),
                ('max_tempo', song_attr_val[1])))
            else:
                filt_rec_params.append(('target_{}'.format(x.lower()), song_attr_val))
    # if not filt_rec_params:

    filt_d = OrderedDict(filt_rec_params)
    return filt_d

#RECOMMENDATION CALL
def get_recs(filters, orig_track_d):
    rec_list = []
    #params examples min_tempo max_tempo, min mode, target_energy
    #may want variable keyword positional arguments here. syntax something like rec(**{'seed_artists': get_rel_arts(orig_track_d), 'min_tempo': 100...})
    #good practice is to use kwargs = {} then recs(**kwargs)
    # st.write(get_genres(orig_track_d))
    #seed_genres=get_genres(orig_track_d)
    recs = sp.recommendations(seed_artists=get_rel_arts(orig_track_d)[:3],seed_tracks=get_tracks(orig_track_d)[:2], limit=100, **filters)
    #
    for x in recs['tracks']:
        if (x['name'] == orig_track_d['track_name']) and (x['artists'][0]['name'] == orig_track_d['arts_name']):
            continue
        rec_track_d = {}
        if len(x['artists']) > 1:
            rec_arts = (", ").join([y['name'] for y in x['artists']])
        else:
            rec_arts = x['artists'][0]['name']
        #rec_d[x['name']] = [rec_arts, x['album']['images'][1]['url'], x['preview_url']]
        rec_track_d['track_uri'] = x['uri']
        rec_track_d['track_name'] = x['name']
        rec_track_d['arts_name'] = rec_arts
        rec_track_d['alb_cov'] = x['album']['images'][1]['url']
        rec_track_d['prev_url'] = x['preview_url']
        rec_list.append(rec_track_d)
    return rec_list



with st.sidebar.beta_expander("See Track Attribute Term Explanations"):
    st.markdown('''
    ## Terms
    - **BPM**: Beats Per Minute
    - **Key**: Group of pitches that make a basis for composition of song.
    - **Danceability**: A track's suitability for dancing based on a
    combination of musical elements including tempo, rhythm stability, beat strength,
    and overall regularity. 0.0 is least danceable and 1.0 is most danceable.
    - **Energy**: Represents a perceptual measure of intensity and
    activity...features contributing to this attribute include dynamic range, perceived
    loudness, timbre, onset rate, and general entropy. 0.0 is low energy and 1.0 is high.
    - **Instrumentalness**: Confidence value of a track not having vocals. The closer the
    value is to 1.0, the greater likelihood the track contains no vocal content.
    - **Valence**: Per Spotify, tracks with high valence sound more positive (e.g. happy, cheerful, euphoric), while tracks with low valence sound more negative (e.g. sad, depressed, angry).
    ''')
st.markdown('<style>h1{font-family:"Franklin Gothic Medium", sans-serif;}</style>', unsafe_allow_html=True)
st.markdown('<style>h4{font-family: "Franklin Gothic Medium", "Franklin Gothic", "ITC Franklin Gothic", Arial, sans-serif; font-weight: lighter;}', unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>Refine Your Recommendations</h1>", unsafe_allow_html=True)
st.markdown('''<h4>Use Spotify's API to find songs related to a track based on criteria
 that you decide. This can be a useful tool for those looking to jam to songs in specific
  keys & tempos, producers in search of reference tracks, and anyone who enjoys finding
   new music.</h4>''', unsafe_allow_html=True)

st.markdown(
    """
<style>
.sidebar .sidebar-content {
    background: #A4E9BD;
    color: black;
}
</style>
""",
    unsafe_allow_html=True,
)


# @st.cache(allow_output_mutation=True)

# while len(res['tracks']['items']) == 0:
#     new = st.write("This track was not found. Please try another: ")
#     res = sp.search("track:{} artist:{}".format(t,a),limit=1)
# song_in = st.text_input("Song Title:", "").lower().strip()
# art_in = st.text_input("Artist:", "").lower().strip()
def playlist_creation():
    sp.user_create_playlist()

def get_res():
    song_in = st.text_input("Song Title:", "").lower().strip()
    art_in = st.text_input("Artist:", "").lower().strip()
    resp = sp.search("track:{} artist:{}".format(song_in,art_in),limit=2)
    return resp

app_use_purpose = st.selectbox("Select Your Use (You'll Be Asked To Confirm Before Creating)", ("Browse", "Create New Playlist", ))

first_res = get_res()
if first_res:
    try:
        while first_res['tracks']['items']:
            search_track_dict = set_search_track_values(first_res)
            audio_features = get_search_aud_feats(search_track_dict['track_uri'])
            display_track(search_track_dict, audio_features)
            # if audio_features:
            #     st.image("circle-of-fifths.jpg", caption="Circle of Fifths", use_column_width=True)
            # song_limit = st.slider("Choose a number of songs to return:")
            filter_options = st.sidebar.multiselect("Select Desired Filters", ["Tempo", "Key", "Danceability", "Energy", "Instrumentalness", "Valence"], key='1')
            final_filters = get_filters(filter_options, audio_features)
            if st.sidebar.button("Get Songs 🎵"):
                r = get_recs(final_filters, search_track_dict)
                placeholder = st.empty()
                prog_bar = placeholder.progress(0)
                i = 0
                aud_feats_lst = []
                for song in r:
                    aud_feats_lst.append(get_search_aud_feats(song['track_uri']))
                    # time.sleep(0.1)
                    i += 1
                    prog_bar.progress(i)
                time.sleep(2)
                placeholder.empty()
                st.balloons()
                final_rec_songs_lst = list(zip(r,aud_feats_lst))
                for song, aud_feat in final_rec_songs_lst:
                    time.sleep(.05)
                    #display_track(song, get_search_aud_feats(song['track_uri']))
                    display_track(song, aud_feat)
            break
    except IndexError:
        st.error("Not found. Check spelling or enter a new track.")
        first_res = get_res()



# if first_res:
#     search_track_dict = set_search_track_values(first_res)
#     audio_features = get_search_aud_feats(search_track_dict['track_uri'])
#     display_track(search_track_dict, audio_features)
#     # if audio_features:
#     #     st.image("circle-of-fifths.jpg", caption="Circle of Fifths", use_column_width=True)
#     # song_limit = st.slider("Choose a number of songs to return:")
#     filter_options = st.sidebar.multiselect("Select Desired Filters", ["Tempo", "Key", "Danceability", "Energy", "Instrumentalness", "Valence"], key='1')
#     final_filters = get_filters(filter_options)
#     if st.sidebar.button("Get Songs 🎵"):
#         r = get_recs(final_filters, search_track_dict)
#         placeholder = st.empty()
#         prog_bar = placeholder.progress(0)
#         i = 0
#         aud_feats_lst = []
#         for song in r:
#             aud_feats_lst.append(get_search_aud_feats(song['track_uri']))
#             # time.sleep(0.1)
#             i += 1
#             prog_bar.progress(i)
#         time.sleep(3)
#         placeholder.empty()
#         st.balloons()
#         final_rec_songs_lst = list(zip(r,aud_feats_lst))
#         for song, aud_feat in final_rec_songs_lst:
#             #display_track(song, get_search_aud_feats(song['track_uri']))
#             display_track(song, aud_feat)
