CHINOOK DATABASE SCHEMA

Tables and Relationships:

1. Artist
   - ArtistId (PRIMARY KEY)
   - Name

2. Album
   - AlbumId (PRIMARY KEY)
   - Title
   - ArtistId (FOREIGN KEY -> Artist.ArtistId)

3. Genre
   - GenreId (PRIMARY KEY)
   - Name

4. Track
   - TrackId (PRIMARY KEY)
   - Name
   - AlbumId (FOREIGN KEY -> Album.AlbumId)
   - GenreId (FOREIGN KEY -> Genre.GenreId)
   - Composer
   - Milliseconds
   - UnitPrice

5. Employee
   - EmployeeId (PRIMARY KEY)
   - FirstName
   - LastName
   - Title
   - ReportsTo (FOREIGN KEY -> Employee.EmployeeId, self-join)
   - BirthDate
   - HireDate
   - Address
   - City
   - State
   - Country
   - PostalCode
   - Phone
   - Fax
   - Email

6. Customer
   - CustomerId (PRIMARY KEY)
   - FirstName
   - LastName
   - Company
   - Address
   - City
   - State
   - Country
   - PostalCode
   - Phone
   - Fax
   - Email
   - SupportRepId (FOREIGN KEY -> Employee.EmployeeId)

7. Invoice
   - InvoiceId (PRIMARY KEY)
   - CustomerId (FOREIGN KEY -> Customer.CustomerId)
   - InvoiceDate
   - BillingAddress
   - BillingCity
   - BillingState
   - BillingCountry
   - BillingPostalCode
   - Total (monetary amount)

8. InvoiceLine
   - InvoiceLineId (PRIMARY KEY)
   - InvoiceId (FOREIGN KEY -> Invoice.InvoiceId)
   - TrackId (FOREIGN KEY -> Track.TrackId)
   - UnitPrice
   - Quantity

9. Playlist
   - PlaylistId (PRIMARY KEY)
   - Name

10. PlaylistTrack
    - PlaylistId (FOREIGN KEY -> Playlist.PlaylistId)
    - TrackId (FOREIGN KEY -> Track.TrackId)
    - PRIMARY KEY (PlaylistId, TrackId)

KEY RELATIONSHIPS:
- Artist produces Albums
- Albums contain Tracks
- Tracks belong to Genres
- Customers make Invoices
- Invoices contain InvoiceLine items (which reference Tracks)
- Employees support Customers
- Playlists group Tracks together
