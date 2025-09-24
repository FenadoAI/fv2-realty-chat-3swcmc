import React, { useState, useEffect } from 'react';
import {
  Plus,
  Edit3,
  Trash2,
  Home,
  DollarSign,
  MapPin,
  Bed,
  Bath,
  Square,
  Calendar,
  Car,
  ArrowLeft,
  Save,
  X
} from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from './ui/dialog';
import { Label } from './ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const API = `${API_BASE}/api`;

const AdminPanel = () => {
  const navigate = useNavigate();
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingProperty, setEditingProperty] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    price: '',
    location: '',
    address: '',
    bedrooms: '',
    bathrooms: '',
    sqft: '',
    property_type: '',
    image_url: '',
    amenities: '',
    year_built: '',
    garage: '',
    lot_size: '',
    mls_number: ''
  });

  useEffect(() => {
    fetchProperties();
  }, []);

  const fetchProperties = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/properties`);
      setProperties(response.data);
    } catch (error) {
      console.error('Error fetching properties:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      price: '',
      location: '',
      address: '',
      bedrooms: '',
      bathrooms: '',
      sqft: '',
      property_type: '',
      image_url: '',
      amenities: '',
      year_built: '',
      garage: '',
      lot_size: '',
      mls_number: ''
    });
    setEditingProperty(null);
  };

  const handleSubmit = async () => {
    try {
      const submitData = {
        ...formData,
        price: parseInt(formData.price) || 0,
        bedrooms: parseInt(formData.bedrooms) || 0,
        bathrooms: parseInt(formData.bathrooms) || 0,
        sqft: parseInt(formData.sqft) || 0,
        year_built: formData.year_built ? parseInt(formData.year_built) : null,
        garage: formData.garage ? parseInt(formData.garage) : null,
        lot_size: formData.lot_size ? parseFloat(formData.lot_size) : null,
        amenities: formData.amenities ? formData.amenities.split(',').map(a => a.trim()) : []
      };

      if (editingProperty) {
        await axios.put(`${API}/properties/${editingProperty.id}`, submitData);
      } else {
        await axios.post(`${API}/properties`, submitData);
      }

      setIsDialogOpen(false);
      resetForm();
      fetchProperties();
    } catch (error) {
      console.error('Error saving property:', error);
      alert('Error saving property. Please check all fields.');
    }
  };

  const handleEdit = (property) => {
    setEditingProperty(property);
    setFormData({
      title: property.title,
      description: property.description,
      price: property.price.toString(),
      location: property.location,
      address: property.address,
      bedrooms: property.bedrooms.toString(),
      bathrooms: property.bathrooms.toString(),
      sqft: property.sqft.toString(),
      property_type: property.property_type,
      image_url: property.image_url,
      amenities: property.amenities.join(', '),
      year_built: property.year_built?.toString() || '',
      garage: property.garage?.toString() || '',
      lot_size: property.lot_size?.toString() || '',
      mls_number: property.mls_number || ''
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (propertyId) => {
    if (window.confirm('Are you sure you want to delete this property?')) {
      try {
        await axios.delete(`${API}/properties/${propertyId}`);
        fetchProperties();
      } catch (error) {
        console.error('Error deleting property:', error);
        alert('Error deleting property.');
      }
    }
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                onClick={() => navigate('/')}
                className="flex items-center"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Website
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Property Management</h1>
                <p className="text-gray-600">Manage your real estate listings</p>
              </div>
            </div>
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogTrigger asChild>
                <Button
                  className="bg-blue-600 hover:bg-blue-700"
                  onClick={resetForm}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Property
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>
                    {editingProperty ? 'Edit Property' : 'Add New Property'}
                  </DialogTitle>
                  <DialogDescription>
                    {editingProperty ? 'Update the property details below.' : 'Fill in the details to add a new property listing.'}
                  </DialogDescription>
                </DialogHeader>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="title">Title</Label>
                    <Input
                      id="title"
                      value={formData.title}
                      onChange={(e) => handleInputChange('title', e.target.value)}
                      placeholder="Property title"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="price">Price ($)</Label>
                    <Input
                      id="price"
                      type="number"
                      value={formData.price}
                      onChange={(e) => handleInputChange('price', e.target.value)}
                      placeholder="0"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="location">Location</Label>
                    <Input
                      id="location"
                      value={formData.location}
                      onChange={(e) => handleInputChange('location', e.target.value)}
                      placeholder="City, State"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="address">Address</Label>
                    <Input
                      id="address"
                      value={formData.address}
                      onChange={(e) => handleInputChange('address', e.target.value)}
                      placeholder="Full address"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bedrooms">Bedrooms</Label>
                    <Input
                      id="bedrooms"
                      type="number"
                      value={formData.bedrooms}
                      onChange={(e) => handleInputChange('bedrooms', e.target.value)}
                      placeholder="0"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bathrooms">Bathrooms</Label>
                    <Input
                      id="bathrooms"
                      type="number"
                      value={formData.bathrooms}
                      onChange={(e) => handleInputChange('bathrooms', e.target.value)}
                      placeholder="0"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="sqft">Square Feet</Label>
                    <Input
                      id="sqft"
                      type="number"
                      value={formData.sqft}
                      onChange={(e) => handleInputChange('sqft', e.target.value)}
                      placeholder="0"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="property_type">Property Type</Label>
                    <Select value={formData.property_type} onValueChange={(value) => handleInputChange('property_type', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="house">House</SelectItem>
                        <SelectItem value="condo">Condo</SelectItem>
                        <SelectItem value="apartment">Apartment</SelectItem>
                        <SelectItem value="townhouse">Townhouse</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="year_built">Year Built</Label>
                    <Input
                      id="year_built"
                      type="number"
                      value={formData.year_built}
                      onChange={(e) => handleInputChange('year_built', e.target.value)}
                      placeholder="YYYY"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="garage">Garage Spaces</Label>
                    <Input
                      id="garage"
                      type="number"
                      value={formData.garage}
                      onChange={(e) => handleInputChange('garage', e.target.value)}
                      placeholder="0"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lot_size">Lot Size (acres)</Label>
                    <Input
                      id="lot_size"
                      type="number"
                      step="0.01"
                      value={formData.lot_size}
                      onChange={(e) => handleInputChange('lot_size', e.target.value)}
                      placeholder="0.00"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="mls_number">MLS Number</Label>
                    <Input
                      id="mls_number"
                      value={formData.mls_number}
                      onChange={(e) => handleInputChange('mls_number', e.target.value)}
                      placeholder="MLS123456"
                    />
                  </div>
                  <div className="md:col-span-2 space-y-2">
                    <Label htmlFor="image_url">Image URL</Label>
                    <Input
                      id="image_url"
                      value={formData.image_url}
                      onChange={(e) => handleInputChange('image_url', e.target.value)}
                      placeholder="https://example.com/image.jpg"
                    />
                  </div>
                  <div className="md:col-span-2 space-y-2">
                    <Label htmlFor="amenities">Amenities (comma separated)</Label>
                    <Input
                      id="amenities"
                      value={formData.amenities}
                      onChange={(e) => handleInputChange('amenities', e.target.value)}
                      placeholder="Pool, Spa, Gym, etc."
                    />
                  </div>
                  <div className="md:col-span-2 space-y-2">
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      value={formData.description}
                      onChange={(e) => handleInputChange('description', e.target.value)}
                      placeholder="Property description..."
                      rows={4}
                    />
                  </div>
                </div>
                <div className="flex justify-end space-x-2">
                  <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                    <X className="h-4 w-4 mr-2" />
                    Cancel
                  </Button>
                  <Button onClick={handleSubmit} className="bg-blue-600 hover:bg-blue-700">
                    <Save className="h-4 w-4 mr-2" />
                    {editingProperty ? 'Update Property' : 'Add Property'}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </div>

      {/* Properties List */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <div className="text-lg text-gray-600">Loading properties...</div>
          </div>
        ) : properties.length === 0 ? (
          <div className="text-center py-12">
            <Home className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No properties found</h3>
            <p className="text-gray-600 mb-4">Get started by adding your first property listing.</p>
            <Button onClick={() => setIsDialogOpen(true)} className="bg-blue-600 hover:bg-blue-700">
              <Plus className="h-4 w-4 mr-2" />
              Add Your First Property
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {properties.map((property) => (
              <Card key={property.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                <div className="relative">
                  <img
                    src={property.image_url}
                    alt={property.title}
                    className="w-full h-48 object-cover"
                  />
                  <Badge
                    className={`absolute top-2 left-2 ${
                      property.status === 'active' ? 'bg-green-600' :
                      property.status === 'pending' ? 'bg-yellow-600' : 'bg-red-600'
                    }`}
                  >
                    {property.status}
                  </Badge>
                </div>
                <CardContent className="p-4">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-lg font-semibold text-gray-900 truncate">{property.title}</h3>
                    <span className="text-xl font-bold text-blue-600 whitespace-nowrap ml-2">
                      {formatPrice(property.price)}
                    </span>
                  </div>
                  <div className="flex items-center text-gray-600 mb-3">
                    <MapPin className="h-4 w-4 mr-1 flex-shrink-0" />
                    <span className="text-sm truncate">{property.location}</span>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-sm text-gray-600 mb-4">
                    <div className="flex items-center">
                      <Bed className="h-4 w-4 mr-1" />
                      {property.bedrooms}
                    </div>
                    <div className="flex items-center">
                      <Bath className="h-4 w-4 mr-1" />
                      {property.bathrooms}
                    </div>
                    <div className="flex items-center">
                      <Square className="h-4 w-4 mr-1" />
                      {property.sqft}
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs text-gray-500 mb-4">
                    <div className="flex items-center">
                      <Calendar className="h-3 w-3 mr-1" />
                      {property.year_built || 'N/A'}
                    </div>
                    <div className="flex items-center">
                      <Car className="h-3 w-3 mr-1" />
                      {property.garage || 0} garage
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">{property.description}</p>
                  <div className="flex justify-end space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEdit(property)}
                    >
                      <Edit3 className="h-4 w-4 mr-1" />
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(property.id)}
                      className="text-red-600 border-red-600 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4 mr-1" />
                      Delete
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminPanel;