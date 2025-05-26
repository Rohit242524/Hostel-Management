function loadSection(section) {
  const content = document.getElementById('mainContent');
  content.innerHTML = '<p>Loading...</p>';

  fetch(`/admin_section/${section}`)
    .then(response => response.text())
    .then(html => {
      content.innerHTML = html;
    })
    .catch(error => {
      content.innerHTML = '<p>Error loading section.</p>';
      console.error(error);
    });
}
