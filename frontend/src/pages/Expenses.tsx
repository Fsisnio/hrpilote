import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { expensesAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const Expenses: React.FC = () => {
  const { user, loading: authLoading } = useAuth();
  const [activeTab, setActiveTab] = useState('reports');
  const [showNewExpenseModal, setShowNewExpenseModal] = useState(false);
  const [showExpenseDetailsModal, setShowExpenseDetailsModal] = useState(false);
  const [showEditExpenseModal, setShowEditExpenseModal] = useState(false);
  const [showAddItemModal, setShowAddItemModal] = useState(false);
  const [showEditItemModal, setShowEditItemModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [selectedExpense, setSelectedExpense] = useState<any>(null);
  const [selectedStatus, setSelectedStatus] = useState('All Statuses');
  const [selectedCategory, setSelectedCategory] = useState('All Categories');
  const [expenseReports, setExpenseReports] = useState<any[]>([]);
  const [expenseItems, setExpenseItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchExpenses = async () => {
      // Wait for authentication to complete
      if (authLoading) {
        return;
      }
      
      // Check if user is authenticated
      if (!user) {
        setError('Please log in to view expenses.');
        setLoading(false);
        return;
      }
      
      try {
        setLoading(true);
        setError(null);
        
        // Fetch expense reports and items from API
        const [reportsResponse, itemsResponse] = await Promise.all([
          expensesAPI.getExpenseReports(),
          expensesAPI.getExpenseItems()
        ]);
        
        setExpenseReports(reportsResponse.data.reports || []);
        setExpenseItems(itemsResponse.data.items || []);
      } catch (err: any) {
        console.error('Error fetching expenses:', err);
        console.error('Error details:', {
          status: err.response?.status,
          statusText: err.response?.statusText,
          data: err.response?.data,
          message: err.message
        });
        
        // Set more specific error message
        if (err.response?.status === 401) {
          setError('Authentication required. Please log in again.');
        } else if (err.response?.status === 403) {
          setError('Access denied. You do not have permission to view expenses.');
        } else if (err.response?.status === 404) {
          setError('Expenses API endpoint not found. Please check server configuration.');
        } else {
          setError(`Failed to fetch expenses: ${err.response?.data?.detail || err.message}`);
        }
        
        // Fallback to mock data on error
        const mockReports = [
          {
            id: 1,
            employee: 'John Doe',
            title: 'Business Trip to New York',
            totalAmount: 1250.00,
            status: 'Paid',
            submittedDate: '2024-01-20',
            approvedDate: '2024-01-22',
            items: 8,
            category: 'Travel'
          },
          {
            id: 2,
            employee: 'Jane Smith',
            title: 'Office Supplies Purchase',
            totalAmount: 450.75,
            status: 'Pending',
            submittedDate: '2024-01-18',
            approvedDate: null,
            items: 5,
            category: 'Office Supplies'
          },
          {
            id: 3,
            employee: 'Mike Johnson',
            title: 'Client Dinner Expenses',
            totalAmount: 320.50,
            status: 'Rejected',
            submittedDate: '2024-01-15',
            approvedDate: '2024-01-17',
            items: 3,
            category: 'Entertainment'
          },
          {
            id: 4,
            employee: 'Sarah Wilson',
            title: 'Conference Registration',
            totalAmount: 850.00,
            status: 'Paid',
            submittedDate: '2024-01-12',
            approvedDate: '2024-01-14',
            items: 1,
            category: 'Training'
          },
          {
            id: 5,
            employee: 'David Brown',
            title: 'Software License Renewal',
            totalAmount: 1200.00,
            status: 'Paid',
            submittedDate: '2024-01-10',
            approvedDate: '2024-01-12',
            items: 1,
            category: 'Software'
          }
        ];
        const mockItems = [
          {
            id: 1,
            description: 'Flight tickets - JFK to LAX',
            amount: 450.00,
            category: 'Travel',
            date: '2024-01-20',
            receipt: 'flight_receipt.pdf'
          },
          {
            id: 2,
            description: 'Hotel accommodation - 3 nights',
            amount: 600.00,
            category: 'Travel',
            date: '2024-01-20',
            receipt: 'hotel_receipt.pdf'
          },
          {
            id: 3,
            description: 'Meals during business trip',
            amount: 200.00,
            category: 'Meals',
            date: '2024-01-20',
            receipt: 'meals_receipt.pdf'
          }
        ];
        setExpenseReports(mockReports);
        setExpenseItems(mockItems);
      } finally {
        setLoading(false);
      }
    };

    fetchExpenses();
  }, [user, authLoading]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Approved': return 'bg-green-100 text-green-800';
      case 'Paid': return 'bg-blue-100 text-blue-800';
      case 'Pending': return 'bg-yellow-100 text-yellow-800';
      case 'Rejected': return 'bg-red-100 text-red-800';
      case 'Draft': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'Travel': return 'bg-blue-100 text-blue-800';
      case 'Office Supplies': return 'bg-purple-100 text-purple-800';
      case 'Entertainment': return 'bg-pink-100 text-pink-800';
      case 'Training': return 'bg-indigo-100 text-indigo-800';
      case 'Software': return 'bg-cyan-100 text-cyan-800';
      case 'Meals': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const totalReports = expenseReports.length;
  const pendingReports = expenseReports.filter(r => r.status === 'Pending').length;
  const approvedReports = expenseReports.filter(r => r.status === 'Approved').length;
  const totalAmount = expenseReports
    .filter(report => report.status === 'Paid')
    .reduce((sum, report) => sum + report.totalAmount, 0);

  const handleRetry = () => {
    setError(null);
    setLoading(true);
    // Trigger a page reload to retry with fresh authentication
    window.location.reload();
  };

  if (authLoading || loading) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="text-center py-12">
          <div className="text-red-600 text-6xl mb-4">⚠️</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Error Loading Expenses</h3>
          <p className="text-gray-600 mb-4">{error}</p>
          <button 
            onClick={handleRetry}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md"
          >
            Retry
          </button>
        </div>
      </Layout>
    );
  }

  const handleViewExpenseDetails = (expense: any) => {
    setSelectedExpense(expense);
    setShowExpenseDetailsModal(true);
  };

  const handleEditExpense = (expense: any) => {
    setSelectedExpense(expense);
    setShowEditExpenseModal(true);
  };

  const handleCreateNewExpense = () => {
    setShowNewExpenseModal(true);
  };

  const handleAddExpenseItem = () => {
    setShowAddItemModal(true);
  };

  const handleCreateExpenseItem = async (itemData: any) => {
    try {
      const response = await expensesAPI.createExpenseItem(itemData);
      setExpenseItems(prev => [response.data, ...prev]);
      setShowAddItemModal(false);
      alert('Expense item created successfully!');
    } catch (error) {
      console.error('Error creating expense item:', error);
      alert('Failed to create expense item. Please try again.');
    }
  };

  const handleEditExpenseItem = (item: any) => {
    setSelectedItem(item);
    setShowEditItemModal(true);
  };

  const handleUpdateExpenseItem = async (itemData: any) => {
    try {
      const response = await expensesAPI.updateExpenseItem(selectedItem.id, itemData);
      setExpenseItems(prev => 
        prev.map(item => 
          item.id === selectedItem.id 
            ? { ...item, ...response.data }
            : item
        )
      );
      setShowEditItemModal(false);
      setSelectedItem(null);
      alert('Expense item updated successfully!');
    } catch (error) {
      console.error('Error updating expense item:', error);
      alert('Failed to update expense item. Please try again.');
    }
  };

  const handleDeleteExpenseItem = async (itemId: number) => {
    if (window.confirm('Are you sure you want to delete this expense item?')) {
      try {
        await expensesAPI.deleteExpenseItem(itemId);
        setExpenseItems(prev => prev.filter(item => item.id !== itemId));
        alert('Expense item deleted successfully!');
      } catch (error) {
        console.error('Error deleting expense item:', error);
        alert('Failed to delete expense item. Please try again.');
      }
    }
  };

  const handleViewReceipt = (receipt: string) => {
    console.log('Viewing receipt:', receipt);
    // TODO: Implement receipt viewer
    alert(`Opening receipt: ${receipt}`);
  };

  const handleCreateExpenseReport = (expenseData: any) => {
    const newExpense = {
      id: expenseReports.length + 1,
      employee: 'Current User', // This would come from auth context
      title: expenseData.title,
      totalAmount: parseFloat(expenseData.amount),
      status: 'Pending',
      submittedDate: new Date().toISOString().split('T')[0],
      approvedDate: null,
      items: 1,
      category: expenseData.category,
      description: expenseData.description
    };
    
    setExpenseReports(prev => [newExpense, ...prev]);
    setShowNewExpenseModal(false);
  };

  const handleUpdateExpense = (expenseData: any) => {
    setExpenseReports(prev => 
      prev.map(expense => 
        expense.id === selectedExpense.id 
          ? { 
              ...expense, 
              title: expenseData.title,
              category: expenseData.category,
              description: expenseData.description,
              totalAmount: parseFloat(expenseData.amount)
            }
          : expense
      )
    );
    setShowEditExpenseModal(false);
    setSelectedExpense(null);
  };

  const handleApproveExpense = (expenseId: number) => {
    console.log('Approving expense:', expenseId);
    setExpenseReports(prev => 
      prev.map(expense => 
        expense.id === expenseId 
          ? { 
              ...expense, 
              status: 'Approved',
              approvedDate: new Date().toISOString().split('T')[0]
            }
          : expense
      )
    );
    alert(`Expense ${expenseId} approved successfully!`);
  };

  const handleRejectExpense = (expenseId: number) => {
    console.log('Rejecting expense:', expenseId);
    setExpenseReports(prev => 
      prev.map(expense => 
        expense.id === expenseId 
          ? { 
              ...expense, 
              status: 'Rejected',
              approvedDate: new Date().toISOString().split('T')[0]
            }
          : expense
      )
    );
    alert(`Expense ${expenseId} rejected!`);
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Expense Management</h1>
            <p className="text-gray-600">Manage expense reports and reimbursements</p>
          </div>
          <button 
            onClick={handleCreateNewExpense}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md"
          >
            New Expense Report
          </button>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <span className="text-blue-600 text-xl">📋</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Reports</p>
                <p className="text-2xl font-semibold text-gray-900">{totalReports}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <span className="text-yellow-600 text-xl">⏳</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Pending</p>
                <p className="text-2xl font-semibold text-gray-900">{pendingReports}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <span className="text-green-600 text-xl">✅</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Approved</p>
                <p className="text-2xl font-semibold text-gray-900">{approvedReports}</p>
              </div>
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <span className="text-purple-600 text-xl">💰</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Amount</p>
                <p className="text-2xl font-semibold text-gray-900">${totalAmount.toFixed(2)}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6">
              <button
                onClick={() => setActiveTab('reports')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'reports'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Expense Reports
              </button>
              <button
                onClick={() => setActiveTab('items')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'items'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Expense Items
              </button>
              <button
                onClick={() => setActiveTab('policies')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'policies'
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Policies
              </button>
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'reports' && (
              <div>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Expense Reports</h3>
                  <div className="flex space-x-2">
                    <select className="border border-gray-300 rounded-md px-3 py-1 text-sm">
                      <option>All Statuses</option>
                      <option>Pending</option>
                      <option>Approved</option>
                      <option>Paid</option>
                      <option>Rejected</option>
                    </select>
                    <select className="border border-gray-300 rounded-md px-3 py-1 text-sm">
                      <option>All Categories</option>
                      <option>Travel</option>
                      <option>Office Supplies</option>
                      <option>Entertainment</option>
                      <option>Training</option>
                      <option>Software</option>
                    </select>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Employee
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Report Title
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Category
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Amount
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Status
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Submitted
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {expenseReports.map((report) => (
                        <tr key={report.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {report.employee}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="text-sm font-medium text-gray-900">{report.title}</div>
                            <div className="text-sm text-gray-500">{report.items} items</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getCategoryColor(report.category)}`}>
                              {report.category}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            ${report.totalAmount.toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(report.status)}`}>
                              {report.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {new Date(report.submittedDate).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex space-x-2">
                              <button 
                                onClick={() => handleViewExpenseDetails(report)}
                                className="text-indigo-600 hover:text-indigo-900"
                              >
                                View
                              </button>
                              {report.status === 'Pending' && (
                                <>
                                  <button 
                                    onClick={() => handleApproveExpense(report.id)}
                                    className="text-green-600 hover:text-green-900"
                                  >
                                    Approve
                                  </button>
                                  <button 
                                    onClick={() => handleRejectExpense(report.id)}
                                    className="text-red-600 hover:text-red-900"
                                  >
                                    Reject
                                  </button>
                                </>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'items' && (
              <div>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Expense Items</h3>
                  <button 
                    onClick={handleAddExpenseItem}
                    className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                  >
                    Add Item
                  </button>
                </div>

                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Description
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Category
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Amount
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Date
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Receipt
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {expenseItems.map((item) => (
                        <tr key={item.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {item.description}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getCategoryColor(item.category)}`}>
                              {item.category}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            ${item.amount.toFixed(2)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {new Date(item.date).toLocaleDateString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            <button 
                              onClick={() => handleViewReceipt(item.receipt)}
                              className="text-indigo-600 hover:text-indigo-900"
                            >
                              {item.receipt}
                            </button>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <div className="flex space-x-2">
                              <button 
                                onClick={() => handleViewExpenseDetails(item)}
                                className="text-indigo-600 hover:text-indigo-900"
                              >
                                View
                              </button>
                              <button 
                                onClick={() => handleEditExpenseItem(item)}
                                className="text-green-600 hover:text-green-900"
                              >
                                Edit
                              </button>
                              <button 
                                onClick={() => handleDeleteExpenseItem(item.id)}
                                className="text-red-600 hover:text-red-900"
                              >
                                Delete
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'policies' && (
              <div className="space-y-6">
                <div className="bg-gray-50 p-6 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-4">Expense Policies</h4>
                  <div className="space-y-4">
                    <div className="bg-white p-4 rounded-lg">
                      <h5 className="font-medium text-gray-900 mb-2">Travel Expenses</h5>
                      <p className="text-sm text-gray-600">
                        Maximum daily allowance: $75 for meals, $200 for accommodation. Flight tickets must be economy class unless approved by manager.
                      </p>
                    </div>
                    <div className="bg-white p-4 rounded-lg">
                      <h5 className="font-medium text-gray-900 mb-2">Office Supplies</h5>
                      <p className="text-sm text-gray-600">
                        All office supplies must be pre-approved for amounts over $100. Receipts required for all purchases.
                      </p>
                    </div>
                    <div className="bg-white p-4 rounded-lg">
                      <h5 className="font-medium text-gray-900 mb-2">Entertainment</h5>
                      <p className="text-sm text-gray-600">
                        Client entertainment expenses require manager approval. Maximum $150 per person per meal.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <button className="bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-lg text-center">
            <div className="text-2xl mb-2">📊</div>
            <div className="font-medium">Expense Reports</div>
          </button>
          <button className="bg-green-600 hover:bg-green-700 text-white p-4 rounded-lg text-center">
            <div className="text-2xl mb-2">💰</div>
            <div className="font-medium">Reimbursements</div>
          </button>
          <button className="bg-purple-600 hover:bg-purple-700 text-white p-4 rounded-lg text-center">
            <div className="text-2xl mb-2">⚙️</div>
            <div className="font-medium">Settings</div>
          </button>
        </div>

        {/* New Expense Report Modal */}
        {showNewExpenseModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">New Expense Report</h3>
                  <button
                    onClick={() => setShowNewExpenseModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>
                
                <form onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.currentTarget);
                  console.log('Creating new expense report:', {
                    title: formData.get('title'),
                    category: formData.get('category'),
                    description: formData.get('description'),
                    amount: formData.get('amount')
                  });
                  handleCreateExpenseReport({
                    title: formData.get('title'),
                    category: formData.get('category'),
                    description: formData.get('description'),
                    amount: formData.get('amount')
                  });
                }}>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Report Title</label>
                      <input
                        type="text"
                        name="title"
                        required
                        placeholder="Enter expense report title"
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Category</label>
                      <select
                        name="category"
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="">Select Category</option>
                        <option value="Travel">Travel</option>
                        <option value="Office Supplies">Office Supplies</option>
                        <option value="Entertainment">Entertainment</option>
                        <option value="Training">Training</option>
                        <option value="Meals">Meals</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Description</label>
                      <textarea
                        name="description"
                        rows={3}
                        placeholder="Describe the expense purpose"
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Total Amount</label>
                      <input
                        type="number"
                        name="amount"
                        min="0"
                        step="0.01"
                        required
                        placeholder="0.00"
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end space-x-3 mt-6">
                    <button
                      type="button"
                      onClick={() => setShowNewExpenseModal(false)}
                      className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                    >
                      Create Report
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Expense Details Modal */}
        {showExpenseDetailsModal && selectedExpense && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-3/4 max-w-4xl shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Expense Details</h3>
                  <button
                    onClick={() => setShowExpenseDetailsModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">{selectedExpense.title || selectedExpense.description}</h4>
                    <p className="text-sm text-gray-600 mb-4">
                      {selectedExpense.description || 'No description provided'}
                    </p>
                    
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Employee:</span>
                        <span className="text-sm font-medium">{selectedExpense.employee || 'N/A'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Category:</span>
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getCategoryColor(selectedExpense.category)}`}>
                          {selectedExpense.category}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Amount:</span>
                        <span className="text-sm font-medium">${selectedExpense.totalAmount?.toFixed(2) || selectedExpense.amount?.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Status:</span>
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(selectedExpense.status)}`}>
                          {selectedExpense.status || 'N/A'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Submitted:</span>
                        <span className="text-sm font-medium">
                          {new Date(selectedExpense.submittedDate || selectedExpense.date).toLocaleDateString()}
                        </span>
                      </div>
                      {selectedExpense.approvedDate && (
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Approved:</span>
                          <span className="text-sm font-medium">{new Date(selectedExpense.approvedDate).toLocaleDateString()}</span>
                        </div>
                      )}
                      {selectedExpense.items && (
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-600">Items:</span>
                          <span className="text-sm font-medium">{selectedExpense.items}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div>
                    <h5 className="font-medium text-gray-900 mb-3">Actions</h5>
                    <div className="space-y-3">
                      {selectedExpense.status === 'Pending' && (
                        <>
                          <button
                            onClick={() => {
                              handleApproveExpense(selectedExpense.id);
                              setShowExpenseDetailsModal(false);
                            }}
                            className="w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md"
                          >
                            Approve Expense
                          </button>
                          <button
                            onClick={() => {
                              handleRejectExpense(selectedExpense.id);
                              setShowExpenseDetailsModal(false);
                            }}
                            className="w-full bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md"
                          >
                            Reject Expense
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => {
                          setShowExpenseDetailsModal(false);
                          handleEditExpense(selectedExpense);
                        }}
                        className="w-full bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md"
                      >
                        Edit Expense
                      </button>
                    </div>
                  </div>
                </div>
                
                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    onClick={() => setShowExpenseDetailsModal(false)}
                    className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Edit Expense Modal */}
        {showEditExpenseModal && selectedExpense && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Edit Expense</h3>
                  <button
                    onClick={() => setShowEditExpenseModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>
                
                <form onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.currentTarget);
                  console.log('Updating expense:', {
                    id: selectedExpense.id,
                    title: formData.get('title'),
                    category: formData.get('category'),
                    description: formData.get('description'),
                    amount: formData.get('amount')
                  });
                  handleUpdateExpense({
                    id: selectedExpense.id,
                    title: formData.get('title'),
                    category: formData.get('category'),
                    description: formData.get('description'),
                    amount: formData.get('amount')
                  });
                }}>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Title/Description</label>
                      <input
                        type="text"
                        name="title"
                        defaultValue={selectedExpense.title || selectedExpense.description}
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Category</label>
                      <select
                        name="category"
                        defaultValue={selectedExpense.category}
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="Travel">Travel</option>
                        <option value="Office Supplies">Office Supplies</option>
                        <option value="Entertainment">Entertainment</option>
                        <option value="Training">Training</option>
                        <option value="Meals">Meals</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Description</label>
                      <textarea
                        name="description"
                        defaultValue={selectedExpense.description}
                        rows={3}
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Amount</label>
                      <input
                        type="number"
                        name="amount"
                        defaultValue={selectedExpense.totalAmount || selectedExpense.amount}
                        min="0"
                        step="0.01"
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end space-x-3 mt-6">
                    <button
                      type="button"
                      onClick={() => setShowEditExpenseModal(false)}
                      className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                    >
                      Update Expense
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Add Expense Item Modal */}
        {showAddItemModal && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Add Expense Item</h3>
                  <button
                    onClick={() => setShowAddItemModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>
                
                <form onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.currentTarget);
                  const itemData = {
                    title: formData.get('title'),
                    description: formData.get('description'),
                    category: formData.get('category'),
                    amount: parseFloat(formData.get('amount') as string),
                    date: formData.get('date'),
                    receipt_number: formData.get('receipt_number'),
                    location: formData.get('location'),
                    vendor: formData.get('vendor'),
                    payment_method: formData.get('payment_method')
                  };
                  handleCreateExpenseItem(itemData);
                }}>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Title</label>
                      <input
                        type="text"
                        name="title"
                        required
                        placeholder="Enter expense title"
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Description</label>
                      <textarea
                        name="description"
                        rows={3}
                        placeholder="Describe the expense"
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Category</label>
                      <select
                        name="category"
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="">Select Category</option>
                        <option value="TRAVEL">Travel</option>
                        <option value="MEALS">Meals</option>
                        <option value="OFFICE_SUPPLIES">Office Supplies</option>
                        <option value="ENTERTAINMENT">Entertainment</option>
                        <option value="TRAINING">Training</option>
                        <option value="SOFTWARE">Software</option>
                        <option value="OTHER">Other</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Amount</label>
                      <input
                        type="number"
                        name="amount"
                        min="0"
                        step="0.01"
                        required
                        placeholder="0.00"
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Date</label>
                      <input
                        type="date"
                        name="date"
                        required
                        defaultValue={new Date().toISOString().split('T')[0]}
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Receipt Number</label>
                      <input
                        type="text"
                        name="receipt_number"
                        placeholder="Enter receipt number"
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Location</label>
                      <input
                        type="text"
                        name="location"
                        placeholder="Enter location"
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Vendor</label>
                      <input
                        type="text"
                        name="vendor"
                        placeholder="Enter vendor name"
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Payment Method</label>
                      <select
                        name="payment_method"
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="CASH">Cash</option>
                        <option value="CREDIT_CARD">Credit Card</option>
                        <option value="DEBIT_CARD">Debit Card</option>
                        <option value="BANK_TRANSFER">Bank Transfer</option>
                        <option value="REIMBURSEMENT">Reimbursement</option>
                      </select>
                    </div>
                  </div>
                  <div className="flex justify-end space-x-3 mt-6">
                    <button
                      type="button"
                      onClick={() => setShowAddItemModal(false)}
                      className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                    >
                      Add Item
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Edit Expense Item Modal */}
        {showEditItemModal && selectedItem && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Edit Expense Item</h3>
                  <button
                    onClick={() => setShowEditItemModal(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>
                
                <form onSubmit={(e) => {
                  e.preventDefault();
                  const formData = new FormData(e.currentTarget);
                  const itemData = {
                    title: formData.get('title'),
                    description: formData.get('description'),
                    category: formData.get('category'),
                    amount: parseFloat(formData.get('amount') as string),
                    date: formData.get('date'),
                    receipt_number: formData.get('receipt_number'),
                    location: formData.get('location'),
                    vendor: formData.get('vendor'),
                    payment_method: formData.get('payment_method')
                  };
                  handleUpdateExpenseItem(itemData);
                }}>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Title</label>
                      <input
                        type="text"
                        name="title"
                        defaultValue={selectedItem.title || selectedItem.description}
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Description</label>
                      <textarea
                        name="description"
                        rows={3}
                        defaultValue={selectedItem.description}
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Category</label>
                      <select
                        name="category"
                        defaultValue={selectedItem.category}
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="TRAVEL">Travel</option>
                        <option value="MEALS">Meals</option>
                        <option value="OFFICE_SUPPLIES">Office Supplies</option>
                        <option value="ENTERTAINMENT">Entertainment</option>
                        <option value="TRAINING">Training</option>
                        <option value="SOFTWARE">Software</option>
                        <option value="OTHER">Other</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Amount</label>
                      <input
                        type="number"
                        name="amount"
                        min="0"
                        step="0.01"
                        defaultValue={selectedItem.amount}
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Date</label>
                      <input
                        type="date"
                        name="date"
                        defaultValue={selectedItem.date}
                        required
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Receipt Number</label>
                      <input
                        type="text"
                        name="receipt_number"
                        defaultValue={selectedItem.receipt}
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Location</label>
                      <input
                        type="text"
                        name="location"
                        defaultValue={selectedItem.location || ''}
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Vendor</label>
                      <input
                        type="text"
                        name="vendor"
                        defaultValue={selectedItem.vendor || ''}
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Payment Method</label>
                      <select
                        name="payment_method"
                        defaultValue={selectedItem.payment_method || 'CASH'}
                        className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="CASH">Cash</option>
                        <option value="CREDIT_CARD">Credit Card</option>
                        <option value="DEBIT_CARD">Debit Card</option>
                        <option value="BANK_TRANSFER">Bank Transfer</option>
                        <option value="REIMBURSEMENT">Reimbursement</option>
                      </select>
                    </div>
                  </div>
                  <div className="flex justify-end space-x-3 mt-6">
                    <button
                      type="button"
                      onClick={() => setShowEditItemModal(false)}
                      className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                    >
                      Update Item
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Expenses; 