/**
 * Returns DOM elem of info card for an org
 * @param {object} org org to display
 * @returns {String} DOM elem of card
 */
function infoCardHTML(org) {

  let orgURL = 'https://maizepages.umich.edu/organization/' + org['WebsiteKey'];
  let photoURL = 'https://se-images.campuslabs.com/clink/images/' + org['ProfilePicture'] + '?preset=small-sq';
  let displayPhoto = photoURL.indexOf("null") >= 0 ? 'none' : 'inline';
  let desc = org['Summary'];
  desc = desc.split(' ').slice(0, 200).join(' ');

  let elem = document.createElement('div');
  elem.className = "card";
  elem.innerHTML = `
        <div onclick="show_similar_to(${org['Id']})">
          <div class="card-body text-center">
            <img src="${photoURL}" style="display: ${displayPhoto}; margin-bottom: 16px;"/>
            <h3 class="card-title">${org['Name']}</h3>
            <p class="card-text text-left">${desc}</p>
          </div>
        </div>
        <div class="card-footer text-center">
          <a href="${orgURL}" target="_blank">View in Maize Pages</a>
        </div>
  `;

  return elem;
}


/**
 * Returns str with time since date
 * @param {Date} date Date with which to calculate diff
 * @returns {String} String with time since date
 */
function timeSince(date) {
  var seconds = Math.floor((new Date() - date) / 1000);

  var interval = seconds / 31536000;

  if (interval > 1) {
    return Math.floor(interval) + " year(s)";
  }
  interval = seconds / 2592000;
  if (interval > 1) {
    return Math.floor(interval) + " month(s)";
  }
  interval = seconds / 86400;
  if (interval > 1) {
    return Math.floor(interval) + " day(s)";
  }
  interval = seconds / 3600;
  if (interval > 1) {
    return Math.floor(interval) + " hour(s)";
  }
  interval = seconds / 60;
  if (interval > 1) {
    return Math.floor(interval) + " minute(s)";
  }
  return Math.floor(seconds) + " second(s)";
}

/**
 * Randomly shuffles array in place.
 * @param {Array} array to shuffle
 */
function shuffle(array) {
  let currentIndex = array.length, randomIndex;

  // While there remain elements to shuffle.
  while (currentIndex > 0) {

    // Pick a remaining element.
    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex--;

    // And swap it with the current element.
    [array[currentIndex], array[randomIndex]] = [
      array[randomIndex], array[currentIndex]];
  }
}