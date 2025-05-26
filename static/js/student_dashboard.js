function loadSection(section) {
  const content = document.getElementById('mainContent');
  content.innerHTML = '<div class="spinner"></div><p>Loading...</p>';

  fetch(`/student_section/${section}`)
    .then(response => response.text())
    .then(html => {
      content.innerHTML = html;
    })
    .catch(error => {
      content.innerHTML = '<p>Error loading section.</p>';
      console.error(error);
    });
}
