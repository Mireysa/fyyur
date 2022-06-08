#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from sre_parse import State
import sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String))
    address = db.Column(db.String(120))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    shows = db.relationship('Show', backref="venue", lazy=True)

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    image_link = db.Column(db.String(500))
    shows = db.relationship('Show', backref="artist", lazy=True)

class Show(db.Model):
    __tablename__ = 'show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    # num_shows should be aggregated based on number of upcoming shows per venue.
    # Querying the database for all venues
    venue_locations = db.session.query(
        Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
    print(venue_locations)

    # Define list to store collection of data we are about to receive
    data = []

    # loop through unique locations
    for venue in venue_locations:
        # Define dict to collect unique locations
        orderedVenues = dict()
        orderedVenues['city'] = venue[0]
        print('Printing the City of the dict orderedVenues: ' +
              orderedVenues['city'])
        orderedVenues['state'] = venue[1]
        print('Printing the State of the dict orderedVenues: ' +
              orderedVenues['state'])
        venue_by_city = db.session.query(Venue.id, Venue.name).filter(
            Venue.city == orderedVenues['city']).all()
        # Define list to store venues
        venues = []
        print('End of Iteration')

        for venue in venue_by_city:
            venueDetails = dict()
            venueDetails['id'] = venue[0]
            venueDetails['name'] = venue[1]
            print(venueDetails)
            # Store current venue into list
            venues.append(venueDetails)
        # Update the dictionary given the current lcoation with the latest venues
        orderedVenues['venues'] = venues
        # Add the collection of the current unique city/state combination + venues to the data list
        data.append(orderedVenues)

    # Return data list with updated information
    return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  response={
    "count": 1,
    "data": [{
      "id": 2,
      "name": "The Dueling Pianos Bar",
      "num_upcoming_shows": 0,
    }]
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # Display the venue page with the given venue_id
    venue = Venue.query.get(venue_id)
    past_shows = []
    upcoming_shows = []
    past_shows_count = 1
    upcoming_shows_count = 4

    # TODO: Pull accurate count of past and upcoming shows.

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "upcoming_shows_count": upcoming_shows_count,
        "past_shows_count": past_shows_count
    }

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # track insertion errors
  insertion_error = False

  # perform form validation
  form = VenueForm(request.form, meta={'csrf': False})
  if not form.validate():
    # if errors are found, flash error
    flash(form.errors)
  else:
    # if form is validated, proceed.
    print('no errors found on venue creation page')
    try:
      venue_name = request.form.get("name")
      venue_city = request.form.get("city")
      venue_state = request.form.get("state")
      venue_address = request.form.get("address")
      venue_phone = request.form.get("phone")
      venue_genres = request.form.getlist("genres")
      venue_website = request.form.get("website_link")
      venue_facebook_link = request.form.get("facebook_link")
      venue_seeking_talent = True if request.form.get("seeking_talent") == 'y' else False
      venue_seeking_description = request.form.get("seeking_description")
      venue_image_link = request.form.get("image_link")

      # insert form data as a new Venue record in the db
      new_venue = Venue(name=venue_name, genres=venue_genres, address=venue_address, city=venue_city, state=venue_state, phone=venue_phone, website=venue_website, facebook_link=venue_facebook_link, seeking_talent=venue_seeking_talent, seeking_description=venue_seeking_description, image_link=venue_image_link)
      db.session.add(new_venue)
      db.session.commit()
    except:
      print(sys.exc_info())
      insertion_error = True
      db.session.rollback()
    finally:
      db.session.close()

  if not insertion_error:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')
  else:
    # on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + venue_name + ' could not be listed.')
  

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # Querying the database for all artists
  artists = Artist.query.with_entities(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  response={
    "count": 1,
    "data": [{
      "id": 4,
      "name": "Guns N Petals",
      "num_upcoming_shows": 0,
    }]
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # Display the artist page with the given artist_id
    artist = Artist.query.get(artist_id)

    # TODO: add logic to pull show data
    past_shows = []
    upcoming_shows = []
    past_shows_count = 1
    upcoming_shows_count = 4

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "seeking_venue": False,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "facebook_link": artist.facebook_link,
        "website_link": artist.website,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "upcoming_shows_count": upcoming_shows_count,
        "past_shows_count": past_shows_count
    }

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist={
    "id": 4,
    "name": "Guns N Petals",
    "genres": ["Rock n Roll"],
    "city": "San Francisco",
    "state": "CA",
    "phone": "326-123-5000",
    "website": "https://www.gunsnpetalsband.com",
    "facebook_link": "https://www.facebook.com/GunsNPetals",
    "seeking_venue": True,
    "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm(request.form, meta={'csrf': False})
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # track insertion errors
  insertion_error = False

  # perform form validation
  form = ArtistForm(request.form, meta={'csrf': False})
  if not form.validate():
    # if errors are found, flash error
    flash(form.errors)
  else:
    # if form is validated, proceed. 
    print('no errors found on artist creation page')
    try:
      artist_name = request.form.get("name")
      artist_city = request.form.get("city")
      artist_state = request.form.get("state")
      artist_phone = request.form.get("phone")
      artist_genres = request.form.getlist("genres")
      artist_website = request.form.get("website_link")
      artist_facebook_link = request.form.get("facebook_link")
      artist_seeking_venue = True if request.form.get("seeking_venue") == 'y' else False
      artist_seeking_description = request.form.get("seeking_description")
      artist_image_link = request.form.get("image_link")

      # insert form data as a new Artist record in the db
      new_artist = Artist(name=artist_name, city=artist_city, state=artist_state, phone=artist_phone, genres=artist_genres, website=artist_website, facebook_link=artist_facebook_link, seeking_venue=artist_seeking_venue, seeking_description=artist_seeking_description, image_link=artist_image_link)
      db.session.add(new_artist)
      db.session.commit()
    except:
      print(sys.exc_info())
      insertion_error = True
      db.session.rollback()
    finally:
      db.session.close()
    
    if not insertion_error:
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
      return render_template('pages/home.html')
    else:
      # on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Artist ' + artist_name + ' could not be listed.')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # Define list to store show information
    data = list()
    # Query all shows
    shows = Show.query.all()
    # Loop through each show in shows query result to obtain details
    for show in shows:
        print(show.venue_id)
        print(show.venue.id)
        # Append show details to data list
        data.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,  # ref parent obj
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,  # ref parent obj
            "artist_image_link": show.artist.image_link,  # ref parent obj
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f%z"),
        })
        print('Show Venue:' + show.venue.name)
    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # track insertion errors
    insertion_error = False

    # obtain form entry
    artist_id = request.form.get("artist_id")
    venue_id = request.form.get("venue_id")
    start_time = request.form.get("start_time")

    # ensure artist and venue id match to existing records
    artist_exists = db.session.query(db.exists().where(Artist.id == artist_id)).scalar()
    venue_exists = db.session.query(db.exists().where(Venue.id == venue_id)).scalar()

    if artist_exists & venue_exists:
      try:
          new_show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
          db.session.add(new_show)
          db.session.commit()
      except:
          print(sys.exc_info())
          insertion_error = True
          db.session.rollback()
      finally:
          db.session.close()
    else: 
      insertion_error = True

    if not insertion_error:
      flash('Show was successfully listed!')
      return render_template('pages/home.html')
    else:
      flash('An error occurred. Show could not be listed.')
      return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
