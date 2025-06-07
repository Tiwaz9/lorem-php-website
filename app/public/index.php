<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Lorem Ipsum PHP Site</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
    img  { max-width: 300px; display: block; margin-top: 20px; }
    #inventory { 
      white-space: pre-wrap; 
      background: #f8f8f8; 
      padding: 10px; 
      border: 1px solid #ddd; 
      margin-top: 20px; 
      font-family: monospace;
    }
    button { padding: 10px 20px; font-size: 1rem; cursor: pointer; }
  </style>
</head>
<body>
  <h1>Welcome to the Lorem Ipsum PHP Site</h1>
  <p>
    <?php
      echo "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
         . "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
         . "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris "
         . "nisi ut aliquip ex ea commodo consequat.";
    ?>
  </p>
  <img src="image.png" alt="Sample Image" />

  <!-- Button to invoke the Lambda via API Gateway -->
  <button id="fetchBtn">Fetch VPC & Subnets Inventory</button>
  <div id="inventory"></div>

  <script>
    // Read the API URL injected by NGINX via fastcgi_param
    const apiUrl = "<?php echo getenv('INVENTORY_API_URL'); ?>";

    document.getElementById('fetchBtn').addEventListener('click', () => {
      const out = document.getElementById('inventory');
      out.textContent = 'Loading…';
      fetch(apiUrl)
        .then(response => {
          if (!response.ok) throw new Error(response.status + ' ' + response.statusText);
          return response.json();
        })
        .then(data => {
          out.textContent = JSON.stringify(data, null, 2);
        })
        .catch(err => {
          out.textContent = 'Error fetching inventory:\n' + err;
        });
    });
  </script>
</body>
</html>
