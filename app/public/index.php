<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <link rel="icon" href="image.png" type="image/png">
  <title>Lorem Ipsum PHP Site</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
    img  { max-width: 300px; display: block; margin-top: 20px; }
    #inventory { margin-top: 20px; white-space: pre-wrap; }
    table { border-collapse: collapse; width: 100%; margin-top: 10px; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; }
    button { padding: 10px 20px; font-size: 1rem; cursor: pointer; }
  </style>
</head>
<body>
  <h1>Welcome to the Lorem Ipsum PHP Site</h1>
  <p>
    <?php echo "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " .
                 "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."; ?>
  </p>
  <img src="image.png" alt="Sample Image" />

  <!-- Fetch Inventory Button -->
  <button id="fetchBtn">Fetch VPC & Subnets Inventory</button>
  <div id="inventory"></div>

  <script>
    const apiUrl = "<?php echo getenv('INVENTORY_API_URL'); ?>";

    function renderTable(data, cols, title) {
      let html = `<h2>${title}</h2><table><thead><tr>`;
      cols.forEach(c => html += `<th>${c}</th>`);
      html += `</tr></thead><tbody>`;
      data.forEach(item => {
        html += `<tr>`;
        cols.forEach(c => {
          let v = item[c];
          if (typeof v === 'object') v = JSON.stringify(v);
          html += `<td>${v != null ? v : ''}</td>`;
        });
        html += `</tr>`;
      });
      html += `</tbody></table>`;
      return html;
    }

    document.getElementById('fetchBtn').addEventListener('click', () => {
      const out = document.getElementById('inventory');
      out.textContent = 'Loading…';
      fetch(apiUrl)
        .then(response => {
          if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          return response.text();
        })
        .then(text => {
          console.log('Raw response:', text);
          let data;
          try {
            data = JSON.parse(text);
          } catch (e) {
            throw new Error('Invalid JSON: ' + e.message);
          }
          if (!data || !Array.isArray(data.vpcs) || !Array.isArray(data.subnets)) {
            throw new Error('Response missing expected vpcs or subnets arrays');
          }
          let content = `<p>Fetched at: ${data.timestamp}</p>`;
          content += renderTable(data.vpcs, ['VpcId','CidrBlock','IsDefault','State','Tags'], 'VPCs');
          content += renderTable(data.subnets, ['SubnetId','VpcId','CidrBlock','AvailabilityZone','State','MapPublicIpOnLaunch'], 'Subnets');
          out.innerHTML = content;
        })
        .catch(err => {
          console.error('Fetch error:', err);
          out.textContent = 'Error fetching inventory: ' + err;
        });
    });
  </script>
</body>
</html>
