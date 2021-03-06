#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from dataclasses import dataclass
import json
from sre_parse import State
import sys
from tkinter import CASCADE
import dateutil.parser
import babel
from flask import (
  Flask, 
  render_template, 
  request, 
  Response, 
  flash, 
  redirect, 
  url_for)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from forms import *
from models import db, Venue, Artist, Show
from datetime import datetime

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
moment = Moment(app)
db.init_app(app)
migrate = Migrate(app, db)

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
  # search on venues with partial string search. case-insensitive.
  # obtain search term
  search_term = request.form.get("search_term")
  # obtain query
  venue_query = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  # obtain response details
  response={
    "count": len(venue_query),
    "data": venue_query
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # Display the venue page with the given venue_id
    venue = Venue.query.get_or_404(venue_id)

    # init variables to track show data
    past_shows = []
    upcoming_shows = []
    
    # check if current venue has/had shows based on current time + date
    for show in venue.shows:
        temp_show = {
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
        }
        if show.start_time <= datetime.now():
            past_shows.append(temp_show)
        else:
            upcoming_shows.append(temp_show)

    # object class to dict
    venue_data = vars(venue)
    venue_data['past_shows'] = past_shows
    venue_data['upcoming_shows'] = upcoming_shows
    venue_data['past_shows_count'] = len(past_shows)
    venue_data['upcoming_shows_count'] = len(upcoming_shows)

    return render_template('pages/show_venue.html', venue=venue_data)

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
  try:
    venue = Venue(
      name=form.name.data,
      city=form.city.data,
      state=form.state.data,
      address=form.address.data,
      phone=form.phone.data,
      genres=form.genres.data,
      facebook_link=form.facebook_link.data,
      image_link=form.image_link.data,
      website=form.website_link.data,
      seeking_talent=form.seeking_talent.data,
      seeking_description=form.seeking_description.data
    )

    # insert validated form data as a new Venue record in the db
    db.session.add(venue)
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
    flash('An error occurred. Venue ' + venue.name + ' could not be listed.')
  

@app.route('/venues/<venue_id>/delete', methods=['POST'])
def delete_venue(venue_id):
  try:
    current_venue = Venue.query.get_or_404(venue_id)
    db.session.delete(current_venue)
    db.session.commit()
    flash('The venue has been removed together with all of its shows.')
    return render_template('pages/home.html')
  except:
    db.session.rollback()
  finally:
    db.session.close()

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # Querying the database for all artists
  artists = Artist.query.with_entities(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # search on artists with partial string search. case-insensitive.
  # obtain search term
  search_term = request.form.get("search_term")
  # obtain query
  artist_query = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  # obtain response details
  response={
    "count": len(artist_query),
    "data": artist_query
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # Display the artist page with the given artist_id
    artist = Artist.query.get_or_404(artist_id)

    # init variables to track show data
    past_shows = []
    upcoming_shows = []

    # check if current artist has/had shows based on current time + date
    for show in artist.shows:
        temp_show = {
            'venue_id': show.venue_id,
            'venue_name': show.venue.name,
            'venue_image_link': show.venue.image_link,
            'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
        }
        if show.start_time <= datetime.now():
            past_shows.append(temp_show)
        else:
            upcoming_shows.append(temp_show)

    # object class to dict
    artist_data = vars(artist)
    artist_data['past_shows'] = past_shows
    artist_data['upcoming_shows'] = upcoming_shows
    artist_data['past_shows_count'] = len(past_shows)
    artist_data['upcoming_shows_count'] = len(upcoming_shows)

    return render_template('pages/show_artist.html', artist=artist_data)

#  DELETE
#  ----------------------------------------------------------------
@app.route('/artists/<artist_id>/delete', methods=['POST'])
def delete_artist(artist_id):
  try:
    current_artist = Artist.query.get_or_404(artist_id)
    db.session.delete(current_artist)
    db.session.commit()
    flash('The artist has been removed together with all of its shows.')
    return render_template('pages/home.html')
  except:
    db.session.rollback()
  finally:
    db.session.close()

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # obtain artist given artist_id
  artist = Artist.query.get_or_404(artist_id)
  # populate form with fields from artist with ID <artist_id>
  form = ArtistForm(obj=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # take values from the form submitted, and update existing
  
  # track insertion errors
  insertion_error = False

  # perform form validation
  form = ArtistForm(request.form, meta={'csrf': False})
  if not form.validate():
    # if errors are found, flash error
    flash(form.errors)
  else:
    # if form is validated, proceed. 
    print('no errors found on artist editing page')
    try:
      # obtain artist
      artist = Artist.query.filter_by(id=artist_id).first()

      # update details
      artist.name = request.form.get("name")
      artist.city = request.form.get("city")
      artist.state = request.form.get("state")
      artist.phone = request.form.get("phone")
      artist.genres = request.form.getlist("genres")
      artist.website = request.form.get("website_link")
      artist.facebook_link = request.form.get("facebook_link")
      artist.seeking_venue = True if request.form.get("seeking_venue") == 'y' else False
      artist.seeking_description = request.form.get("seeking_description")
      artist.image_link = request.form.get("image_link")

      # commit changes
      db.session.commit()
    except:
      insertion_error = True
      db.session.rollback()
    finally:
      db.session.close()

    if not insertion_error:
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully updated!')
      return render_template('pages/home.html')
    else:
      # on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Artist ' + artist.name + ' could not be updated.')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # obtain venue given venue_id
  venue = Venue.query.get_or_404(venue_id)
  # populate form with values from venue with ID <venue_id>
  form = VenueForm(obj=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # take values from the form submitted, and update existing
 
  # track insertion errors
  insertion_error = False

  # perform form validation
  form = VenueForm(request.form, meta={'csrf': False})
  if not form.validate():
    # if errors are found, flash error
    flash(form.errors)
  else:
    # if form is validated, proceed. 
    print('no errors found on venue editing page')
    try:
      # obtain venue
      venue = Venue.query.filter_by(id=venue_id).first()
      # update details
      venue.name = request.form.get("name")
      venue.city = request.form.get("city")
      venue.state = request.form.get("state")
      venue.phone = request.form.get("phone")
      venue.genres = request.form.getlist("genres")
      venue.website = request.form.get("website_link")
      venue.facebook_link = request.form.get("facebook_link")
      venue.seeking_talent = True if request.form.get("seeking_talent") == 'y' else False
      venue.seeking_description = request.form.get("seeking_description")
      venue.image_link = request.form.get("image_link")

      # commit changes
      db.session.commit()
    except:
      insertion_error = True
      db.session.rollback()
    finally:
      db.session.close()

    if not insertion_error:
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully updated!')
      return render_template('pages/home.html')
    else:
      # on unsuccessful db insert, flash an error instead.
      flash('An error occurred. Venue ' + venue.name + ' could not be updated.')

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
  try:
    artist = Artist(
      name=form.name.data,
      city=form.city.data,
      state=form.state.data,
      phone=form.phone.data,
      genres=form.genres.data,
      facebook_link=form.facebook_link.data,
      image_link=form.image_link.data,
      website=form.website_link.data,
      seeking_venue=form.seeking_venue.data,
      seeking_description=form.seeking_description.data
    )

    # insert form data as a new Artist record in the db
    db.session.add(artist)
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
    flash('An error occurred. Artist could not be listed.')

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

    form = ShowForm(request.form, meta={'csrf': False})
    try:
      show = Show(
        artist_id = form.artist_id.data,
        venue_id = form.venue_id.data,
        start_time = form.start_time.data
      )
      db.session.add(show)
      db.session.commit()
    except:
      print(sys.exc_info())
      insertion_error = True
      db.session.rollback()
    finally:
      db.session.close()

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
