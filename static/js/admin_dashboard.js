// admin_dashboard.js
function loadSection(section) {
  const content = document.getElementById('mainContent');
  content.innerHTML = '<p>Loading...</p>';

  let url;
  if (section === 'students') {
    url = '/view_students';
  } else if (section === 'rooms') {
    url = '/manage_rooms';
  } else if (section === 'bookings') {
    url = '/view_bookings';
  } else if (section === 'complaints') {
    url = '/handle_complaints';
  }

  fetch(url)
    .then(response => response.text())
    .then(html => {
      content.innerHTML = html;
    })
    .catch(error => {
      content.innerHTML = '<p>Error loading section.</p>';
      console.error(error);
    });
}