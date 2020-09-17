import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for,abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import *
from flask_migrate import Migrate
from datetime import datetime
from difflib import get_close_matches
import sys
from models import Artist, Venue, Show, db_setup

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
now = datetime.utcnow()
migrate = Migrate(app, db)
db_setup(app)

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#



# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

    data = []

    cities = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state)

    for city in cities:
        venues_in_city = db.session.query(Venue.id, Venue.name).filter(Venue.city == city[0]).filter(
            Venue.state == city[1])
        data.append({
            "city": city[0],
            "state": city[1],
            "venues": venues_in_city
        })

    return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
# TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
# seach for Hop should return "The Musical Hop".
# search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
def search_venues():
    search_venue = '%{}%'.format(request.form.get('search_term'))
    venue = Venue.query.filter(Venue.name.ilike(search_venue))
    response = {
        "count": venue.count(),
        "data": venue.all()
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    venue = Venue.query.get(venue_id)

    count_upcoming_shows = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time > datetime.now()).all()
    upcoming_shows = []
    count_past_shows = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id).filter(Show.start_time < datetime.now()).all()
    past_shows = []

    for show in count_past_shows:
            past_shows.append({
                "artist_id": show.artist_id,
                "artist_name": show.show_registered.name,
                "artist_image_link": show.show_registered.image_link,
                "start_time": show.start_time
            })

    for show in count_upcoming_shows:
        upcoming_shows.append({
            "artist_id": show.artist_id,
            "artist_name": show.show_registered.name,
            "artist_image_link": show.show_registered.image_link,
            "start_time": show.start_time
        })
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
            "past_shows" : past_shows,
            "upcoming_shows": upcoming_shows,
            "past_shows_count": len(past_shows),
            "upcoming_shows_count": len(upcoming_shows),
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
    error = False
    try:
        form = VenueForm()
        create_venue = Venue(
            name=form.name.data,
            city=form.city.data,
            address=form.address.data,
            state=form.state.data,
            phone=form.phone.data,
            genres=form.genres.data,
            facebook_link=form.facebook_link.data,
            image_link=form.image_link.data
        )
        db.session.add(create_venue)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    if not error:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')


@app.route('/venues/<int:venue_id>', methods=['POST'])
def delete_venue(venue_id):
    try:
        venue = Venue.query.filter_by(id=venue_id).first_or_404()
        session = db.object_session(venue)
        session.delete(venue)
        session.commit()
        flash('The venue has been removed together with all of its shows.')
        return render_template('pages/home.html')
    except ValueError:
        flash('It was not possible to delete this Venue')
    return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = []
    artists = Artist.query.all()
    for artist in artists:
        data_add= {
            'id' : artist.id,
            'name' : artist.name
        }
        data.append(data_add)
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_venue = '%{}%'.format(request.form.get('search_term'))
    artist = Artist.query.filter(Artist.name.ilike(search_venue))
    response = {
        "count": artist.count(),
        "data": artist.all()
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)

    count_upcoming_shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(
        Show.start_time > datetime.now()).all()
    upcoming_shows = []
    count_past_shows = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id).filter(
        Show.start_time < datetime.now()).all()
    past_shows = []

    for show in count_past_shows:
        past_shows.append({
            "venue_id": show.venue_id,
            "venue_name": show.show_organised.name,
            "venue_image_link": show.show_organised.image_link,
            "start_time": show.start_time
        })

    for show in count_upcoming_shows:
        upcoming_shows.append({
            "venue_id": show.venue_id,
            "venue_name": show.show_organised.name,
            "venue_image_link": show.show_organised.image_link,
            "start_time": show.start_time
        })

    data = {
        'id' : artist.id,
        'name' : artist.name,
        'genres' : [artist.genres],
        'city' : artist.city,
        'state' : artist.state,
        'phone' : artist.phone,
        'website' : artist.website,
        'facebook_link' : artist.facebook_link,
        'seeking_venue' : artist.seeking_venue,
        'seeking_description' : artist.seeking_description,
        'image_link' : artist.image_link,
        'past_shows' : past_shows,
        'upcoming_shows' : upcoming_shows,
        'past_shows_count' : len(past_shows),
        'upcoming_shows_count' : len(upcoming_shows)
        }
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)

    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)
    artist_data = Artist.query.get(artist_id)
    try:
        if artist_data:
            setattr(artist_data, 'name', request.form['name'])
            setattr(artist_data, 'city', request.form['city'])
            setattr(artist_data, 'state', request.form['state'])
            setattr(artist_data, 'phone', request.form['phone'])
            setattr(artist_data, 'image_link', request.form['image_link'])
            setattr(artist_data, 'genres', request.form.getlist('genres'))
            setattr(artist_data, 'facebook_link', request.form['facebook_link'])
            Artist.update(artist_data)
            flash('Artist ' + request.form['name'] + 'was successfully updated!')
    except:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)

    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)
    venue = Venue.query.get(venue_id)

    try:
        if venue:
            setattr(venue, 'name', request.form['name'])
            setattr(venue, 'city', request.form['city'])
            setattr(venue, 'state', request.form['state'])
            setattr(venue, 'address', request.form['address'])
            setattr(venue, 'phone', request.form['phone'])
            setattr(venue, 'genres', request.form.getlist('genres'))
            setattr(venue, 'facebook_link', request.form['facebook_link'])
            setattr(venue, 'image_link', request.form['image_link'])
            Venue.update(venue)
            flash('Venue ' + request.form['name'] + 'was successfully updated!')
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
        flash(f'An error occurred. Venue could not be changed.')
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    try:
        form = ArtistForm()
        create_artist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            genres=form.genres.data,
            facebook_link=form.facebook_link.data,
            image_link=form.image_link.data,
        )
        db.session.add(create_artist)
        db.session.commit()
    except:
        db.session.rollback()
        error = True
        sys.exc_info()
    finally:
        db.session.close()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shows = db.session.query(Show).join(Venue, Artist).filter(Show.start_time > datetime.now()).all()
    data = []
    for show in shows:
        data_show = {
            'venue_id' : show.venue_id,
            'venue_name' : show.show_organised.name,
            'artist_id' : show.artist_id,
            'artist_name' : show.show_registered.name,
            'artist_image_link' : show.show_registered.image_link,
            'start_time' : show.start_time
        }
        data.append(data_show)
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    try:
        form = ShowForm()
        show_create = Show(
        venue_id=form.venue_id.data,
        artist_id=form.artist_id.data,
        start_time=form.start_time.data
        )
        db.session.add(show_create)
        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info())
        error = True
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Show could not be listed.')
    if not error:
        flash('Show was successfully listed!')

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

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
