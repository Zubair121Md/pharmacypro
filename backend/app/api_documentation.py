"""
Comprehensive API Documentation Generator
Version: 2.0
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import inspect
from fastapi import APIRouter, FastAPI
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field
import yaml

class APIEndpoint(BaseModel):
    """API endpoint documentation model"""
    path: str
    method: str
    summary: str
    description: str
    tags: List[str]
    parameters: List[Dict[str, Any]] = []
    request_body: Optional[Dict[str, Any]] = None
    responses: Dict[str, Dict[str, Any]] = {}
    security: List[Dict[str, Any]] = []
    examples: List[Dict[str, Any]] = []

class APIDocumentation:
    """Comprehensive API documentation generator"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.documentation = {
            'info': {
                'title': 'Pharmacy Revenue Management System API',
                'version': '2.0',
                'description': 'Comprehensive API for managing pharmacy revenue data, analytics, and reporting',
                'contact': {
                    'name': 'API Support',
                    'email': 'support@pharmacy-revenue.com'
                },
                'license': {
                    'name': 'MIT',
                    'url': 'https://opensource.org/licenses/MIT'
                }
            },
            'servers': [
                {
                    'url': 'http://localhost:8000',
                    'description': 'Development server'
                },
                {
                    'url': 'https://api.pharmacy-revenue.com',
                    'description': 'Production server'
                }
            ],
            'paths': {},
            'components': {
                'schemas': {},
                'securitySchemes': {
                    'BearerAuth': {
                        'type': 'http',
                        'scheme': 'bearer',
                        'bearerFormat': 'JWT'
                    }
                }
            },
            'tags': []
        }
    
    def generate_documentation(self) -> Dict[str, Any]:
        """Generate comprehensive API documentation"""
        self._extract_routes()
        self._generate_schemas()
        self._generate_tags()
        self._add_examples()
        
        return self.documentation
    
    def _extract_routes(self):
        """Extract all routes from the FastAPI app"""
        for route in self.app.routes:
            if isinstance(route, APIRoute):
                self._document_route(route)
    
    def _document_route(self, route: APIRoute):
        """Document a single route"""
        path = route.path
        methods = route.methods
        
        if path not in self.documentation['paths']:
            self.documentation['paths'][path] = {}
        
        for method in methods:
            if method in ['HEAD', 'OPTIONS']:
                continue
            
            endpoint_doc = self._create_endpoint_documentation(route, method)
            self.documentation['paths'][path][method.lower()] = endpoint_doc
    
    def _create_endpoint_documentation(self, route: APIRoute, method: str) -> Dict[str, Any]:
        """Create documentation for a single endpoint"""
        endpoint_doc = {
            'summary': route.summary or f"{method} {route.path}",
            'description': route.description or f"Endpoint for {method} {route.path}",
            'tags': route.tags or ['General'],
            'parameters': self._extract_parameters(route),
            'responses': self._extract_responses(route),
            'security': self._extract_security(route)
        }
        
        # Add request body if applicable
        if method in ['POST', 'PUT', 'PATCH']:
            endpoint_doc['requestBody'] = self._extract_request_body(route)
        
        return endpoint_doc
    
    def _extract_parameters(self, route: APIRoute) -> List[Dict[str, Any]]:
        """Extract parameters from route"""
        parameters = []
        
        # Path parameters
        for param in route.path_params:
            parameters.append({
                'name': param,
                'in': 'path',
                'required': True,
                'schema': {'type': 'string'},
                'description': f'Path parameter: {param}'
            })
        
        # Query parameters (simplified)
        if 'query' in str(route.dependant):
            parameters.append({
                'name': 'query',
                'in': 'query',
                'required': False,
                'schema': {'type': 'string'},
                'description': 'Query parameters'
            })
        
        return parameters
    
    def _extract_responses(self, route: APIRoute) -> Dict[str, Dict[str, Any]]:
        """Extract response schemas"""
        responses = {
            '200': {
                'description': 'Successful response',
                'content': {
                    'application/json': {
                        'schema': {'type': 'object'}
                    }
                }
            },
            '400': {
                'description': 'Bad request',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'error': {'type': 'string'},
                                'detail': {'type': 'string'}
                            }
                        }
                    }
                }
            },
            '401': {
                'description': 'Unauthorized',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'detail': {'type': 'string'}
                            }
                        }
                    }
                }
            },
            '403': {
                'description': 'Forbidden',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'detail': {'type': 'string'}
                            }
                        }
                    }
                }
            },
            '500': {
                'description': 'Internal server error',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'properties': {
                                'error': {'type': 'string'},
                                'detail': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        }
        
        return responses
    
    def _extract_security(self, route: APIRoute) -> List[Dict[str, Any]]:
        """Extract security requirements"""
        # Check if route requires authentication
        if any('auth' in str(dep) for dep in route.dependant.dependencies):
            return [{'BearerAuth': []}]
        return []
    
    def _extract_request_body(self, route: APIRoute) -> Dict[str, Any]:
        """Extract request body schema"""
        return {
            'required': True,
            'content': {
                'application/json': {
                    'schema': {'type': 'object'}
                }
            }
        }
    
    def _generate_schemas(self):
        """Generate common schemas"""
        schemas = {
            'User': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'username': {'type': 'string'},
                    'email': {'type': 'string'},
                    'role': {'type': 'string', 'enum': ['user', 'admin', 'super_admin']},
                    'area': {'type': 'string'},
                    'created_at': {'type': 'string', 'format': 'date-time'}
                }
            },
            'LoginRequest': {
                'type': 'object',
                'properties': {
                    'username': {'type': 'string'},
                    'password': {'type': 'string'}
                },
                'required': ['username', 'password']
            },
            'TokenResponse': {
                'type': 'object',
                'properties': {
                    'access_token': {'type': 'string'},
                    'token_type': {'type': 'string'}
                }
            },
            'FileUploadResponse': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'filename': {'type': 'string'},
                    'records_processed': {'type': 'integer'},
                    'success': {'type': 'boolean'}
                }
            },
            'AnalyticsData': {
                'type': 'object',
                'properties': {
                    'summary_metrics': {'type': 'object'},
                    'revenue_analytics': {'type': 'object'},
                    'monthly_trends': {'type': 'array'},
                    'top_performers': {'type': 'object'}
                }
            },
            'ErrorResponse': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'detail': {'type': 'string'},
                    'error_code': {'type': 'string'},
                    'timestamp': {'type': 'string'}
                }
            }
        }
        
        self.documentation['components']['schemas'] = schemas
    
    def _generate_tags(self):
        """Generate API tags"""
        tags = [
            {
                'name': 'Authentication',
                'description': 'User authentication and authorization endpoints'
            },
            {
                'name': 'File Upload',
                'description': 'File upload and processing endpoints'
            },
            {
                'name': 'Analytics',
                'description': 'Revenue analytics and reporting endpoints'
            },
            {
                'name': 'Administration',
                'description': 'System administration and user management endpoints'
            },
            {
                'name': 'Unmatched Records',
                'description': 'Management of unmatched pharmacy records'
            },
            {
                'name': 'Data Export',
                'description': 'Data export and reporting endpoints'
            },
            {
                'name': 'Advanced Features',
                'description': 'Advanced features including ML, audit logs, and backups'
            },
            {
                'name': 'Health Check',
                'description': 'System health and status endpoints'
            }
        ]
        
        self.documentation['tags'] = tags
    
    def _add_examples(self):
        """Add examples to endpoints"""
        examples = {
            '/api/v1/auth/login': {
                'post': {
                    'examples': {
                        'successful_login': {
                            'summary': 'Successful login',
                            'value': {
                                'username': 'admin',
                                'password': 'admin123'
                            }
                        }
                    }
                }
            },
            '/api/v1/analytics/dashboard': {
                'get': {
                    'examples': {
                        'dashboard_response': {
                            'summary': 'Dashboard data response',
                            'value': {
                                'summary_metrics': {
                                    'total_revenue': 150000.0,
                                    'total_invoices': 1250,
                                    'total_pharmacies': 45,
                                    'average_order_value': 120.0,
                                    'growth_rate': 15.5
                                },
                                'revenue_analytics': {
                                    'pharmacy_revenue': [
                                        {'pharmacy_name': 'Gayathri Medicals', 'total_revenue': 25000.0}
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }
        
        # Add examples to documentation
        for path, methods in examples.items():
            if path in self.documentation['paths']:
                for method, example_data in methods.items():
                    if method in self.documentation['paths'][path]:
                        self.documentation['paths'][path][method].update(example_data)

class UserGuideGenerator:
    """Generate user guide documentation"""
    
    def __init__(self):
        self.guide = {
            'title': 'Pharmacy Revenue Management System - User Guide',
            'version': '2.0',
            'sections': []
        }
    
    def generate_user_guide(self) -> Dict[str, Any]:
        """Generate comprehensive user guide"""
        self._add_overview()
        self._add_authentication_guide()
        self._add_file_upload_guide()
        self._add_analytics_guide()
        self._add_administration_guide()
        self._add_troubleshooting_guide()
        
        return self.guide
    
    def _add_overview(self):
        """Add system overview"""
        self.guide['sections'].append({
            'title': 'System Overview',
            'content': {
                'description': 'The Pharmacy Revenue Management System is a comprehensive solution for managing pharmacy revenue data, generating analytics, and creating reports.',
                'features': [
                    'User authentication and role-based access control',
                    'Excel file upload and processing',
                    'Pharmacy ID generation and matching',
                    'Revenue analytics and reporting',
                    'ML-based pharmacy matching',
                    'Audit logging and compliance',
                    'Automated backup and recovery',
                    'Data export in multiple formats'
                ],
                'user_roles': {
                    'User': 'Can upload files, view analytics, and export data',
                    'Admin': 'Can manage users, view audit logs, and access advanced features',
                    'Super Admin': 'Full system access including backup management'
                }
            }
        })
    
    def _add_authentication_guide(self):
        """Add authentication guide"""
        self.guide['sections'].append({
            'title': 'Authentication',
            'content': {
                'login_process': [
                    'Navigate to the login page',
                    'Enter your username and password',
                    'Click "Login" to authenticate',
                    'You will be redirected to the dashboard upon successful login'
                ],
                'password_requirements': [
                    'Minimum 8 characters',
                    'Must contain at least one letter and one number',
                    'Special characters are allowed but not required'
                ],
                'troubleshooting': {
                    'forgot_password': 'Contact your system administrator to reset your password',
                    'account_locked': 'Contact your system administrator if your account is locked',
                    'invalid_credentials': 'Double-check your username and password'
                }
            }
        })
    
    def _add_file_upload_guide(self):
        """Add file upload guide"""
        self.guide['sections'].append({
            'title': 'File Upload',
            'content': {
                'supported_formats': ['Excel (.xlsx)', 'CSV (.csv)'],
                'file_requirements': {
                    'master_data': {
                        'required_columns': [
                            'REP_Names', 'Doctor_Names', 'Doctor_ID', 'Pharmacy_Names',
                            'Pharmacy_ID', 'Product_Names', 'Product_ID', 'Product_Price', 'HQ', 'AREA'
                        ],
                        'max_size': '10MB',
                        'max_rows': '50,000'
                    },
                    'invoice_data': {
                        'required_columns': ['Pharmacy Name', 'Product', 'Quantity', 'Amount'],
                        'max_size': '10MB',
                        'max_rows': '50,000'
                    }
                },
                'upload_process': [
                    'Navigate to the File Upload page',
                    'Select the file type (Master Data or Invoice Data)',
                    'Drag and drop your file or click to browse',
                    'Wait for processing to complete',
                    'Review the results and any unmatched records'
                ],
                'data_quality_checks': [
                    'Column name validation',
                    'Data type validation',
                    'Required field validation',
                    'Duplicate detection',
                    'Format validation'
                ]
            }
        })
    
    def _add_analytics_guide(self):
        """Add analytics guide"""
        self.guide['sections'].append({
            'title': 'Analytics and Reporting',
            'content': {
                'dashboard_overview': {
                    'summary_metrics': 'Key performance indicators and totals',
                    'revenue_analytics': 'Revenue breakdown by pharmacy, doctor, and rep',
                    'monthly_trends': 'Revenue trends over time',
                    'top_performers': 'Best performing pharmacies and products'
                },
                'available_reports': [
                    'Pharmacy Revenue Report',
                    'Doctor Revenue Report',
                    'Rep Revenue Report',
                    'Monthly Trends Report',
                    'Custom Analytics Report'
                ],
                'export_formats': ['Excel (.xlsx)', 'CSV (.csv)', 'PDF (.pdf)'],
                'data_filtering': [
                    'Date range filtering',
                    'Pharmacy filtering',
                    'Product filtering',
                    'Area filtering'
                ]
            }
        })
    
    def _add_administration_guide(self):
        """Add administration guide"""
        self.guide['sections'].append({
            'title': 'Administration',
            'content': {
                'user_management': {
                    'creating_users': [
                        'Navigate to Admin Panel > User Management',
                        'Click "Add New User"',
                        'Fill in user details',
                        'Assign appropriate role and area',
                        'Click "Create User"'
                    ],
                    'managing_users': [
                        'View user list in Admin Panel',
                        'Edit user details by clicking on user',
                        'Deactivate users if needed',
                        'Reset passwords when required'
                    ]
                },
                'system_monitoring': {
                    'audit_logs': 'View all system activities and user actions',
                    'system_stats': 'Monitor system performance and usage',
                    'error_logs': 'Review system errors and issues'
                },
                'backup_management': {
                    'creating_backups': 'Create full system backups manually',
                    'restoring_backups': 'Restore system from backup files',
                    'backup_scheduling': 'Set up automated backup schedules'
                }
            }
        })
    
    def _add_troubleshooting_guide(self):
        """Add troubleshooting guide"""
        self.guide['sections'].append({
            'title': 'Troubleshooting',
            'content': {
                'common_issues': {
                    'file_upload_fails': {
                        'causes': ['Invalid file format', 'Missing required columns', 'File too large'],
                        'solutions': ['Check file format', 'Verify column names', 'Reduce file size']
                    },
                    'analytics_not_loading': {
                        'causes': ['No data uploaded', 'Database connection issues', 'Permission problems'],
                        'solutions': ['Upload data first', 'Check system status', 'Verify user permissions']
                    },
                    'login_issues': {
                        'causes': ['Incorrect credentials', 'Account locked', 'System maintenance'],
                        'solutions': ['Verify username/password', 'Contact administrator', 'Wait for maintenance to complete']
                    }
                },
                'error_codes': {
                    'AUTH_001': 'Invalid username or password',
                    'AUTH_002': 'Account locked due to multiple failed attempts',
                    'FILE_001': 'Invalid file format',
                    'FILE_002': 'File size exceeds limit',
                    'DB_001': 'Database connection error',
                    'PERM_001': 'Insufficient permissions'
                },
                'contact_support': {
                    'email': 'support@pharmacy-revenue.com',
                    'phone': '+1-800-PHARMACY',
                    'hours': 'Monday-Friday, 9 AM - 6 PM EST'
                }
            }
        })

def generate_complete_documentation(app: FastAPI) -> Dict[str, Any]:
    """Generate complete API and user documentation"""
    # Generate API documentation
    api_doc = APIDocumentation(app)
    api_documentation = api_doc.generate_documentation()
    
    # Generate user guide
    user_guide_gen = UserGuideGenerator()
    user_guide = user_guide_gen.generate_user_guide()
    
    # Combine documentation
    complete_documentation = {
        'api_documentation': api_documentation,
        'user_guide': user_guide,
        'generated_at': datetime.now().isoformat(),
        'version': '2.0'
    }
    
    return complete_documentation

def save_documentation_to_files(app: FastAPI, output_dir: str = "docs"):
    """Save documentation to files"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Generate documentation
    documentation = generate_complete_documentation(app)
    
    # Save API documentation as OpenAPI JSON
    with open(output_path / "api_documentation.json", "w") as f:
        json.dump(documentation['api_documentation'], f, indent=2)
    
    # Save API documentation as OpenAPI YAML
    with open(output_path / "api_documentation.yaml", "w") as f:
        yaml.dump(documentation['api_documentation'], f, default_flow_style=False)
    
    # Save user guide
    with open(output_path / "user_guide.json", "w") as f:
        json.dump(documentation['user_guide'], f, indent=2)
    
    # Save complete documentation
    with open(output_path / "complete_documentation.json", "w") as f:
        json.dump(documentation, f, indent=2)
    
    print(f"Documentation saved to {output_path}")
    return output_path
